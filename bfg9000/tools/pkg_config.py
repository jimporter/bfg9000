import argparse
import os
import re
import subprocess

from . import tool
from .common import check_which, Command, guess_command, make_command_converter
from .. import log, options as opts, shell
from ..exceptions import PackageResolutionError, PackageVersionError
from ..file_types import Directory, HeaderDirectory
from ..iterutils import iterate, listify
from ..objutils import memoize_method
from ..packages import Package, PackageKind
from ..path import Path, Root
from ..shell import posix as pshell, which
from ..versioning import check_version, SpecifierSet, Version

_lib_dirs_parser = argparse.ArgumentParser()
_lib_dirs_parser.add_argument('-L', action='append', dest='lib_dirs')

_include_dirs_parser = argparse.ArgumentParser()
_include_dirs_parser.add_argument('-I', action='append', dest='include_dirs')

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
        'include_dirs': (['--cflags-only-I'], _shell_split),
        'other_cflags': (['--cflags-only-other'], _shell_split),
        'lib_dirs': (['--libs-only-L'], _shell_split),
        'other_ldflags': (['--libs-only-other'], _shell_split),
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
                return cmd, True
            except IOError:
                pass

        # Try the default command candidate.
        return check_which(default, env.variables)

    def __init__(self, env):
        super().__init__(env, command=('pkg_config',) + self._get_command(env))

    def _call(self, cmd, names, type, static=False, msvc_syntax=False,
              options=[]):
        result = cmd + listify(names) + self._options[type][0] + options
        if static:
            result.append('--static')
        if msvc_syntax:
            result.append('--msvc-syntax')
        return result

    def run(self, names, type, *args, extra_env=None, installed=None,
            **kwargs):
        if installed is True:
            extra_env = dict(PKG_CONFIG_DISABLE_UNINSTALLED='1',
                             **(extra_env or {}))
        elif installed is False:
            names = [i + '-uninstalled' for i in iterate(names)]

        result = super().run(names, type, *args, extra_env=extra_env,
                             **kwargs).strip()
        if self._options[type][1]:
            return self._options[type][1](result)
        return result


class PkgConfigPackage(Package):
    def __init__(self, pkg_config, name, submodules=None,
                 specifier=SpecifierSet(), pcnames=None, *, format,
                 kind=PackageKind.any, system=True, deps=None,
                 search_path=None):
        super().__init__(name, submodules, format=format, deps=deps)

        self._pkg_config = pkg_config
        self._env = ({'PKG_CONFIG_PATH': shell.join_paths(search_path)}
                     if search_path else {})
        self.pcnames = pcnames if pcnames is not None else [name]

        try:
            version = self._call(self.pcnames[0], 'version')
            version = Version(version) if version else None
        except subprocess.CalledProcessError:
            raise PackageResolutionError("unable to find package '{}'"
                                         .format(name))

        if version:
            check_version(version, specifier, name, PackageVersionError)
        self.version = version
        self.specifier = specifier
        self.static = kind == PackageKind.static
        self.system = system

    @memoize_method
    def _call(self, *args, extra_env=None, **kwargs):
        final_env = dict(**self._env, **extra_env) if extra_env else self._env
        return self._pkg_config.run(*args, extra_env=final_env, **kwargs)

    def include_dirs(self, **kwargs):
        args = self._call(self.pcnames, 'include_dirs', self.static, **kwargs)
        inc_dirs = _include_dirs_parser.parse_known_args(args)[0].include_dirs
        return [Path(i, Root.absolute) for i in inc_dirs or []]

    def lib_dirs(self, **kwargs):
        args = self._call(self.pcnames, 'lib_dirs', self.static, **kwargs)
        lib_dirs = _lib_dirs_parser.parse_known_args(args)[0].lib_dirs
        return [Path(i, Root.absolute) for i in lib_dirs or []]

    def _get_rpaths(self):
        extra_env = {'PKG_CONFIG_ALLOW_SYSTEM_LIBS': '1'}

        def rpaths_for(installed):
            try:
                return self.lib_dirs(extra_env=extra_env, installed=installed)
            except shell.CalledProcessError:
                return None

        uninstalled = rpaths_for(installed=False)
        installed = rpaths_for(installed=True)

        if uninstalled is None or uninstalled == installed:
            return opts.option_list(opts.rpath_dir(i) for i in installed)
        else:
            return opts.option_list(
                (opts.rpath_dir(i, 'uninstalled') for i in uninstalled),
                (opts.rpath_dir(i, 'installed') for i in installed or []),
            )

    def _get_install_name_changes(self, pcnames=None):
        if pcnames is None:
            pcnames = self.pcnames

        def install_names_for(installed):
            try:
                return self._call(pcnames, 'install_names', self.static,
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
        requires = self._call(pcnames, 'requires')
        for i in requires:
            result.extend(self._get_install_name_changes(i))

        return result

    def compile_options(self, compiler, *, raw=False):
        flags = self._call(self.pcnames, 'other_cflags', self.static,
                           not raw and compiler.flavor == 'msvc')
        # Get include paths separately so we can selectively use them as
        # "system" includes; this helps ensure that warnings in external
        # headers don't break the build when using `-Werror`.
        incdirs = opts.option_list(
            opts.include_dir(HeaderDirectory(i, system=self.system))
            for i in self.include_dirs()
        )
        return flags + incdirs

    def link_options(self, linker, *, raw=False):
        flags = self._call(self.pcnames, 'other_ldflags', self.static,
                           not raw and linker.flavor == 'msvc')
        libdirs = opts.option_list(opts.lib_dir(Directory(i))
                                   for i in self.lib_dirs())

        # XXX: How should we ensure that these libs are linked statically when
        # necessary?
        libs = self._call(self.pcnames, 'ldlibs', self.static,
                          not raw and linker.flavor == 'msvc')
        libs = opts.option_list(opts.lib_literal(i) for i in libs)

        # Add extra link options as needed for platform-specific oddities.
        extra_opts = opts.option_list()
        if not raw and not self.static:
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

        return flags + libdirs + libs + extra_opts

    def path(self):
        return self._call(self.pcnames[0], 'path')

    def __repr__(self):
        return '<{}({!r}, {!r})>'.format(
            type(self).__name__, self.name, str(self.version)
        )


# A package automatically generated for us by mopack. This is useful when
# generating our own pkg-config file, so that we don't add this one as a
# requirement (it's only temporary, after all).
class GeneratedPkgConfigPackage(PkgConfigPackage):
    pass


def resolve(env, name, *args, generated=False, **kwargs):
    type = GeneratedPkgConfigPackage if generated else PkgConfigPackage
    pkg = type(env.tool('pkg_config'), name, *args, **kwargs)
    log.info('found package {!r} version {} via pkg-config in {}'
             .format(pkg.name, pkg.version, os.path.normpath(pkg.path())))
    return pkg
