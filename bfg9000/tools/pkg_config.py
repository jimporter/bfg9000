from .hooks import tool
from .utils import SimpleCommand


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
