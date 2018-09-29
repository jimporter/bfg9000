import argparse
import subprocess

from . import tool
from .common import SimpleCommand
from .. import options as opts, shell
from ..exceptions import PackageResolutionError, PackageVersionError
from ..iterutils import first
from ..objutils import memoize
from ..packages import Package, PackageKind
from ..path import Path, Root
from ..versioning import check_version, Version


@tool('pkg_config')
class PkgConfig(SimpleCommand):
    _options = {
        'version': ['--modversion'],
        'cflags': ['--cflags'],
        'lib_dirs': ['--libs-only-L'],
        'ldflags': ['--libs-only-L', '--libs-only-other'],
        'ldlibs': ['--libs-only-l'],
    }

    def __init__(self, env):
        SimpleCommand.__init__(self, env, name='pkg_config',
                               env_var='PKG_CONFIG', default='pkg-config')

    def _call(self, cmd, name, type, static=False, msvc_syntax=False):
        result = cmd + [name] + self._options[type]
        if static:
            result.append('--static')
        if msvc_syntax:
            result.append('--msvc-syntax')
        return result


class PkgConfigPackage(Package):
    def __init__(self, name, format, specifier, kind, pkg_config):
        self._pkg_config = pkg_config

        try:
            version = Version(self._pkg_config.run(name, 'version').strip())
        except subprocess.CalledProcessError:
            raise PackageResolutionError("unable to find package '{}'"
                                         .format(name))

        check_version(version, specifier, name, PackageVersionError)
        self.version = version
        self.specifier = specifier
        self.static = kind == PackageKind.static
        Package.__init__(self, name, format)

    @memoize
    def _call(self, *args, **kwargs):
        return shell.split(self._pkg_config.run(*args, **kwargs).strip(),
                           type=opts.option_list)

    def compile_options(self, compiler, output):
        return self._call(self.name, 'cflags', self.static,
                          compiler.flavor == 'msvc')

    def link_options(self, linker, output):
        flags = self._call(self.name, 'ldflags', self.static,
                           linker.flavor == 'msvc')

        # XXX: How should we ensure that these libs are linked statically when
        # necessary?
        libs = self._call(self.name, 'ldlibs', self.static,
                          linker.flavor == 'msvc')
        libs = opts.option_list(opts.lib_literal(i) for i in libs)

        if first(output).format != 'elf' or self.static:
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

    def __repr__(self):
        return '<PkgConfigPackage({!r}, {!r})>'.format(
            self.name, str(self.version)
        )


def resolve(env, name, format, version=None, kind=PackageKind.any):
    return PkgConfigPackage(name, format, version, kind,
                            env.tool('pkg_config'))
