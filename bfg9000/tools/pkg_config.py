from .hooks import tool
from .utils import check_which


@tool('pkg_config')
class Install(object):
    rule_name = command_var = 'pkg_config'

    def __init__(self, env):
        self.command = env.getvar('PKG_CONFIG', 'pkg-config')
        check_which(self.command)

    def version(self, cmd, name):
        return [cmd, '--modversion', name]

    def _flags(self, cmd, options, name, msvc_syntax):
        result = [cmd] + options
        if msvc_syntax:
            result.append('--msvc-syntax')
        result.append(name)
        return result

    def cflags(self, cmd, name, msvc_syntax=False):
        return self._flags(cmd, ['--cflags'], name, msvc_syntax)

    def ldflags(self, cmd, name, msvc_syntax=False):
        return self._flags(cmd, ['--libs-only-L', '--libs-only-other'], name,
                           msvc_syntax)

    def ldlibs(self, cmd, name, msvc_syntax=False):
        return self._flags(cmd, ['--libs-only-l'], name, msvc_syntax)
