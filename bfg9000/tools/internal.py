from .hooks import tool
from ..platforms import platform_name
from ..safe_str import escaped_str, jbos, safe_str


@tool('bfg9000')
class Bfg9000(object):
    rule_name = command_var = 'bfg9000'

    def __init__(self, env):
        self.command = env.getvar('BFG9000', env.bfgdir.append('bfg9000'))

    def regenerate(self, cmd, builddir):
        return [cmd, 'refresh', builddir]


@tool('depfixer')
class Depfixer(object):
    rule_name = command_var = 'depfixer'

    def __init__(self, env):
        default = env.bfgdir.append('bfg9000-depfixer')
        self.command = env.getvar('DEPFIXER', default)

    def __call__(self, cmd, depfile):
        return cmd + ' < ' + depfile + ' >> ' + depfile


if platform_name() == 'windows':
    @tool('setenv')
    class SetEnv(object):
        rule_name = command_var = 'setenv'

        def __init__(self, env):
            default = env.bfgdir.append('bfg9000-setenv')
            self.command = env.getvar('SETENV', default)

        def __call__(self, cmd, env):
            if env:
                eq = escaped_str('=')
                return [cmd] + [jbos(safe_str(name), eq, safe_str(value))
                                for name, value in env.iteritems()] + ['--']
            return []
