from . import tool
from .common import SimpleCommand
from ..safe_str import shell_literal
from ..shell import shell_list


@tool('bfg9000')
class Bfg9000(SimpleCommand):
    def __init__(self, env):
        SimpleCommand.__init__(self, env, name='bfg9000', env_var='BFG9000',
                               default=env.bfgdir.append('bfg9000'))

    def _call(self, cmd, builddir):
        return cmd + ['refresh', builddir]


@tool('depfixer')
class Depfixer(SimpleCommand):
    def __init__(self, env):
        SimpleCommand.__init__(self, env, name='depfixer', env_var='DEPFIXER',
                               default=env.bfgdir.append('bfg9000-depfixer'))

    def _call(self, cmd, depfile):
        return shell_list(cmd + [shell_literal('<'), depfile,
                                 shell_literal('>>'), depfile])


@tool('jvmoutput')
class JvmOutput(SimpleCommand):
    def __init__(self, env):
        SimpleCommand.__init__(
            self, env, name='jvmoutput', env_var='JVMOUTPUT',
            default=env.bfgdir.append('bfg9000-jvmoutput')
        )

    def _call(self, cmd, output, subcmd):
        return cmd + ['-o', output] + subcmd
