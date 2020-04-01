import argparse
import subprocess

from . import tool
from .common import SimpleCommand
from .. import log, options as opts
from ..exceptions import PackageResolutionError, PackageVersionError
from ..objutils import memoize
from ..packages import Package, PackageKind
from ..path import Path, Root
from ..shell import posix as pshell
from ..versioning import check_version, Version


@tool('pkg_config')
class PkgConfig(SimpleCommand):
    # Map command names to pkg-config flags and whether they should be treated
    # as shell arguments.
    _options = {
        'version': (['--modversion'], False),
        'path': (['--variable=pcfiledir'], False),
        'cflags': (['--cflags'], True),
        'lib_dirs': (['--libs-only-L'], True),
        'ldflags': (['--libs-only-L', '--libs-only-other'], True),
        'ldlibs': (['--libs-only-l'], True),
    }

    def __init__(self, env):
        super().__init__(env, name='pkg_config', env_var='PKG_CONFIG',
                         default='pkg-config')

    def _call(self, cmd, name, type, static=False, msvc_syntax=False):
        result = cmd + [name] + self._options[type][0]
        if static:
            result.append('--static')
        if msvc_syntax:
            result.append('--msvc-syntax')
        return result

    def run(self, name, type, *args, **kwargs):
        result = super().run(name, type, *args, **kwargs).strip()
        if self._options[type][1]:
            return pshell.split(result, type=opts.option_list, escapes=True)
        return result


class PkgConfigPackage(Package):
    def __init__(self, name, format, specifier, kind, pkg_config):
        super().__init__(name, format)
        self._pkg_config = pkg_config

        try:
            version = Version(self._call(name, 'version'))
        except subprocess.CalledProcessError:
            raise PackageResolutionError("unable to find package '{}'"
                                         .format(name))

        check_version(version, specifier, name, PackageVersionError)
        self.version = version
        self.specifier = specifier
        self.static = kind == PackageKind.static

    @memoize
    def _call(self, *args, **kwargs):
        return self._pkg_config.run(*args, **kwargs)

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

        if linker.builder.object_format != 'elf' or self.static:
            return flags + libs

        # pkg-config packages don't generally include rpath information, so we
        # need to generate it ourselves.
        dir_args = self._call(self.name, 'lib_dirs', self.static,
                              linker.flavor == 'msvc',
                              env={'PKG_CONFIG_ALLOW_SYSTEM_LIBS': '1'})

        parser = argparse.ArgumentParser()
        parser.add_argument('-L', action='append', dest='lib_dirs')
        lib_dirs = parser.parse_known_args(dir_args)[0].lib_dirs or []
        rpaths = opts.option_list(opts.rpath_dir(Path(i, Root.absolute))
                                  for i in lib_dirs)

        return flags + libs + rpaths

    def path(self):
        return self._call(self.name, 'path')

    def __repr__(self):
        return '<PkgConfigPackage({!r}, {!r})>'.format(
            self.name, str(self.version)
        )


def resolve(env, name, format, version=None, kind=PackageKind.any):
    package = PkgConfigPackage(name, format, version, kind,
                               env.tool('pkg_config'))
    log.info('found package {!r} version {} via pkg-config in {!r}'
             .format(name, package.version, package.path()))
    return package
