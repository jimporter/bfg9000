import subprocess

from .hooks import tool
from .utils import SimpleCommand
from .. import shell
from ..file_types import Package
from ..versioning import check_version, Version


@tool('pkg_config')
class PkgConfig(SimpleCommand):
    rule_name = command_var = 'pkg_config'
    _options = {
        'version': ['--modversion'],
        'cflags': ['--cflags'],
        'ldflags': ['--libs-only-L', '--libs-only-other'],
        'ldlibs': ['--libs-only-l']
    }

    def __init__(self, env):
        SimpleCommand.__init__(self, env, 'PKG_CONFIG', 'pkg-config')

    def __call__(self, cmd, name, type, static=False, msvc_syntax=False):
        result = [cmd, name] + self._options[type]
        if static:
            result.append('--static')
        if msvc_syntax:
            result.append('--msvc-syntax')
        return result


class PkgConfigPackage(Package):
    def __init__(self, name, kind, pkg_config):
        self.name = name
        self.static = kind == 'static'
        self._pkg_config = pkg_config
        try:
            self.version = Version(self._pkg_config.run(
                self.name, 'version'
            ).strip())
        except subprocess.CalledProcessError:
            raise ValueError("unable to find package '{}'".format(name))

    def cflags(self, compiler, output):
        return shell.split(self._pkg_config.run(
            self.name, 'cflags', self.static, compiler.flavor == 'msvc'
        ).strip())

    def ldflags(self, linker, output):
        return shell.split(self._pkg_config.run(
            self.name, 'ldflags', self.static, linker.flavor == 'msvc'
        ).strip())

    def ldlibs(self, linker, output):
        # XXX: How should we ensure that these libs are linked statically when
        # necessary?
        return shell.split(self._pkg_config.run(
            self.name, 'ldlibs', self.static, linker.flavor == 'msvc'
        ).strip())

    def __repr__(self):
        return '<PkgConfigPackage({!r}, {!r})>'.format(
            self.name, str(self.version)
        )


def resolve(env, name, kind='any', version=None):
    pkg = PkgConfigPackage(name, kind, env.tool('pkg_config'))
    check_version(pkg.version, version, name)
    return pkg
