from .hooks import tool
from .utils import Command
from ..platforms import platform_name
from ..safe_str import escaped_str, jbos, safe_str
from ..shell import shell_list


@tool('bfg9000')
class Bfg9000(Command):
    rule_name = command_var = 'bfg9000'

    def __init__(self, env):
        cmd = env.getvar('BFG9000', env.bfgdir.append('bfg9000'))
        Command.__init__(self, env, cmd)

    def regenerate(self, cmd, builddir):
        return [cmd, 'refresh', builddir]


@tool('depfixer')
class Depfixer(Command):
    rule_name = command_var = 'depfixer'

    def __init__(self, env):
        cmd = env.getvar('DEPFIXER', env.bfgdir.append('bfg9000-depfixer'))
        Command.__init__(self, env, cmd)

    def __call__(self, cmd, depfile):
        return shell_list([cmd, escaped_str('<'), depfile, escaped_str('>>'),
                           depfile])


@tool('jvmoutput')
class JvmOutput(Command):
    rule_name = command_var = 'depfixer'

    def __init__(self, env):
        cmd = env.getvar('JVMOUTPUT', env.bfgdir.append('bfg9000-jvmoutput'))
        Command.__init__(self, env, cmd)

    def __call__(self, cmd, output):
        return shell_list([cmd, escaped_str('>'), output])


if platform_name() == 'windows':
    @tool('setenv')
    class SetEnv(Command):
        rule_name = command_var = 'setenv'

        def __init__(self, env):
            cmd = env.getvar('SETENV', env.bfgdir.append('bfg9000-setenv'))
            Command.__init__(self, env, cmd)

        def __call__(self, cmd, env):
            if env:
                eq = escaped_str('=')
                return [cmd] + [jbos(safe_str(name), eq, safe_str(value))
                                for name, value in env.iteritems()] + ['--']
            return []
