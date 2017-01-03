import subprocess

from .hooks import tool
from .utils import SimpleCommand
from .. import shell
from ..file_types import Package
from ..versionutils import check_version, Version


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

    def __call__(self, cmd, name, type, msvc_syntax=False):
        result = [cmd, name] + self._options[type]
        if msvc_syntax:
            result.append('--msvc-syntax')
        return result


class PkgConfigPackage(Package):
    def __init__(self, name, pkg_config):
        self.name = name
        self._pkg_config = pkg_config
        try:
            self.version = Version(self._pkg_config.run(
                self.name, 'version'
            ).strip())
        except subprocess.CalledProcessError:
            raise ValueError("unable to find package '{}'".format(name))

    def cflags(self, compiler, output):
        return shell.split(self._pkg_config.run(
            self.name, 'cflags', compiler.flavor == 'msvc'
        ).strip())

    def ldflags(self, linker, output):
        return shell.split(self._pkg_config.run(
            self.name, 'ldflags', linker.flavor == 'msvc'
        ).strip())

    def ldlibs(self, linker, output):
        return shell.split(self._pkg_config.run(
            self.name, 'ldlibs', linker.flavor == 'msvc'
        ).strip())


def resolve(env, name, version=None):
    pkg = PkgConfigPackage(name, env.tool('pkg_config'))
    check_version(pkg.version, version, name)
    return pkg
