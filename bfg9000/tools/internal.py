from . import tool
from .utils import Command
from ..platforms import platform_name
from ..safe_str import jbos, safe_str, shell_literal
from ..shell import shell_list


@tool('bfg9000')
class Bfg9000(Command):
    rule_name = command_var = 'bfg9000'

    def __init__(self, env):
        cmd = env.getvar('BFG9000', env.bfgdir.append('bfg9000'))
        Command.__init__(self, env, cmd)

    def _call(self, cmd, builddir):
        return [cmd, 'refresh', builddir]


@tool('depfixer')
class Depfixer(Command):
    rule_name = command_var = 'depfixer'

    def __init__(self, env):
        cmd = env.getvar('DEPFIXER', env.bfgdir.append('bfg9000-depfixer'))
        Command.__init__(self, env, cmd)

    def _call(self, cmd, depfile):
        return shell_list([cmd, shell_literal('<'), depfile,
                           shell_literal('>>'), depfile])


@tool('jvmoutput')
class JvmOutput(Command):
    rule_name = command_var = 'jvmoutput'

    def __init__(self, env):
        cmd = env.getvar('JVMOUTPUT', env.bfgdir.append('bfg9000-jvmoutput'))
        Command.__init__(self, env, cmd)

    def _call(self, cmd, output, subcmd):
        return [cmd, '-o', output] + subcmd


if platform_name() == 'windows':
    @tool('setenv')
    class SetEnv(Command):
        rule_name = command_var = 'setenv'

        def __init__(self, env):
            cmd = env.getvar('SETENV', env.bfgdir.append('bfg9000-setenv'))
            Command.__init__(self, env, cmd)

        def _call(self, cmd, env):
            if env:
                eq = shell_literal('=')
                return [cmd] + [jbos(safe_str(name), eq, safe_str(value))
                                for name, value in env.iteritems()] + ['--']
            return []
