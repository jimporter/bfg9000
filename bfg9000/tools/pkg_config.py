import argparse
import os
import re
import subprocess

from . import tool
from .common import check_which, Command, guess_command, make_command_converter
from .. import log, options as opts, shell
from ..exceptions import PackageResolutionError, PackageVersionError
from ..objutils import memoize_method
from ..packages import Package, PackageKind
from ..path import Path, Root
from ..shell import posix as pshell, which
from ..versioning import check_version, Version

_lib_dirs_parser = argparse.ArgumentParser()
_lib_dirs_parser.add_argument('-L', action='append', dest='lib_dirs')

_c_to_pkgconf = make_command_converter([
    (re.compile(r'gcc(?:-[\d.]+)?(?:-(?:posix|win32))?'), 'pkg-config'),
])


def _shell_split(output):
    return pshell.split(output, type=opts.option_list, escapes=True)


def _requires_split(output):
    return [i.split(' ')[0] for i in output.split('\n') if i]


@tool('pkg_config')
class PkgConfig(Command):
    # Map command names to pkg-config flags and whether they should be treated
    # as shell arguments.
    _options = {
        'version': (['--modversion'], None),
        'requires': (['--print-requires'], _requires_split),
        'path': (['--variable=pcfiledir'], None),
        'install_names': (['--variable=install_names'], _shell_split),
        'cflags': (['--cflags'], _shell_split),
        'lib_dirs': (['--libs-only-L'], _shell_split),
        'ldflags': (['--libs-only-L', '--libs-only-other'], _shell_split),
        'ldlibs': (['--libs-only-l'], _shell_split),
    }

    @staticmethod
    def _get_command(env):
        cmd = env.getvar('PKG_CONFIG')
        if cmd:
            return check_which(cmd, env.variables)

        # We don't have an explicitly-set command from the environment, so try
        # to guess what the right command would be based on the C compiler
        # command.
        default = 'pkg-config'
        sibling = env.builder('c').compiler
        guessed_cmd = guess_command(sibling, _c_to_pkgconf)

        # If the guessed command is the same as the default command candidate,
        # skip it. This will keep us from logging a useless info message that
        # we guessed the default value for the command.
        if guessed_cmd is not None and guessed_cmd != default:
            try:
                cmd = which(guessed_cmd, env.variables)
                log.info('guessed pkg-config {!r} from c compiler {!r}'
                         .format(guessed_cmd, shell.join(sibling.command)))
                return cmd
            except IOError:
                pass

        # Try the default command candidate.
        return check_which(default, env.variables)

    def __init__(self, env):
        super().__init__(env, command=('pkg_config', self._get_command(env)))

    def _call(self, cmd, name, type, static=False, msvc_syntax=False):
        result = cmd + [name] + self._options[type][0]
        if static:
            result.append('--static')
        if msvc_syntax:
            result.append('--msvc-syntax')
        return result

    def run(self, name, type, *args, extra_env=None, installed=None, **kwargs):
        if installed is True:
            extra_env = dict(PKG_CONFIG_DISABLE_UNINSTALLED='1',
                             **(extra_env or {}))
        elif installed is False:
            name += '-uninstalled'

        result = super().run(name, type, *args, extra_env=extra_env,
                             **kwargs).strip()
        if self._options[type][1]:
            return self._options[type][1](result)
        return result


class PkgConfigPackage(Package):
    def __init__(self, name, format, specifier, kind, pkg_config, deps=None,
                 search_path=None):
        super().__init__(name, format, deps)
        self._pkg_config = pkg_config
        self._env = {'PKG_CONFIG_PATH': search_path} if search_path else {}

        try:
            version = Version(self._call(name, 'version'))
        except subprocess.CalledProcessError:
            raise PackageResolutionError("unable to find package '{}'"
                                         .format(name))

        check_version(version, specifier, name, PackageVersionError)
        self.version = version
        self.specifier = specifier
        self.static = kind == PackageKind.static

    @memoize_method
    def _call(self, *args, extra_env=None, **kwargs):
        final_env = dict(**self._env, **extra_env) if extra_env else self._env
        return self._pkg_config.run(*args, extra_env=final_env, **kwargs)

    def _get_rpaths(self):
        extra_env = {'PKG_CONFIG_ALLOW_SYSTEM_LIBS': '1'}

        def rpaths_for(installed):
            try:
                args = self._call(self.name, 'lib_dirs', self.static,
                                  extra_env=extra_env, installed=installed)
            except shell.CalledProcessError:
                return None
            lib_dirs = _lib_dirs_parser.parse_known_args(args)[0].lib_dirs
            return [Path(i, Root.absolute) for i in lib_dirs or []]

        uninstalled = rpaths_for(installed=False)
        installed = rpaths_for(installed=True)

        if uninstalled is None or uninstalled == installed:
            return opts.option_list(opts.rpath_dir(i) for i in installed)
        else:
            return opts.option_list(
                (opts.rpath_dir(i, 'uninstalled') for i in uninstalled),
                (opts.rpath_dir(i, 'installed') for i in installed or []),
            )

    def _get_install_name_changes(self, name=None):
        if name is None:
            name = self.name

        def install_names_for(installed):
            try:
                return self._call(name, 'install_names', self.static,
                                  installed=installed)
            except shell.CalledProcessError:
                return None

        uninstalled = install_names_for(installed=False)
        installed = install_names_for(installed=True)
        if ( uninstalled is None or installed is None or
             uninstalled == installed ):
            result = opts.option_list()
        else:
            result = opts.option_list(opts.install_name_change(i, j)
                                      for i, j in zip(uninstalled, installed))

        # Recursively get install_name changes for public requirements.
        requires = self._call(name, 'requires')
        for i in requires:
            result.extend(self._get_install_name_changes(i))

        return result

    def compile_options(self, compiler):
        return self._call(self.name, 'cflags', self.static,
                          compiler.flavor == 'msvc')

    def link_options(self, linker):
        flags = self._call(self.name, 'ldflags', self.static,
                           linker.flavor == 'msvc')

        # XXX: How should we ensure that these libs are linked statically when
        # necessary?
        libs = self._call(self.name, 'ldlibs', self.static,
                          linker.flavor == 'msvc')
        libs = opts.option_list(opts.lib_literal(i) for i in libs)

        # Add extra link options as needed for platform-specific oddities.
        extra_opts = opts.option_list()
        if not self.static:
            if linker.builder.object_format == 'elf':
                # pkg-config packages don't generally include rpath
                # information, so we need to generate it ourselves.
                extra_opts = self._get_rpaths()
            elif linker.builder.object_format == 'mach-o':
                # When using uninstalled variants of pkg-config packages, we
                # should check if there are any install_names set that we need
                # to update when installing. For more information, see the
                # pkg-config builtin.
                extra_opts = self._get_install_name_changes()

        return flags + libs + extra_opts

    def path(self):
        return self._call(self.name, 'path')

    def __repr__(self):
        return '<PkgConfigPackage({!r}, {!r})>'.format(
            self.name, str(self.version)
        )


def resolve(env, name, format, version=None, kind=PackageKind.any):
    package = PkgConfigPackage(name, format, version, kind,
                               env.tool('pkg_config'))
    log.info('found package {!r} version {} via pkg-config in {}'
             .format(name, package.version, os.path.normpath(package.path())))
    return package
