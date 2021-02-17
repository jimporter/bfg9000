from . import tool
from .common import SimpleCommand
from ..safe_str import shell_literal
from ..shell import shell_list


@tool('bfg9000')
class Bfg9000(SimpleCommand):
    def __init__(self, env):
        super().__init__(env, name='bfg9000', env_var='BFG9000',
                         default=env.bfgdir.append('bfg9000'))

    def _call_refresh(self, cmd, builddir):
        return cmd + ['refresh', builddir]

    def _call_run(self, cmd, *, args, initial=False):
        result = cmd + ['run']
        if initial:
            result.append('-I')
        return result + ['--'] + args

    def _call(self, cmd, subcmd, *args, **kwargs):
        try:
            return getattr(self, '_call_' + subcmd)(cmd, *args, **kwargs)
        except AttributeError:
            raise TypeError('unknown subcommand {!r}'.format(subcmd))


@tool('depfixer')
class Depfixer(SimpleCommand):
    def __init__(self, env):
        super().__init__(env, name='depfixer', env_var='DEPFIXER',
                         default=env.bfgdir.append('bfg9000-depfixer'))

    def _call(self, cmd, depfile):
        return shell_list(cmd + [shell_literal('<'), depfile,
                                 shell_literal('>>'), depfile])


@tool('jvmoutput')
class JvmOutput(SimpleCommand):
    def __init__(self, env):
        super().__init__(env, name='jvmoutput', env_var='JVMOUTPUT',
                         default=env.bfgdir.append('bfg9000-jvmoutput'))

    def _call(self, cmd, output, subcmd):
        return cmd + ['-o', output, '--'] + subcmd


@tool('rccdep')
class RccDep(SimpleCommand):
    def __init__(self, env):
        super().__init__(env, name='rccdep', env_var='RCCDEP',
                         default=env.bfgdir.append('bfg9000-rccdep'))

    def _call(self, cmd, subcmd, depfile):
        return cmd + subcmd + ['-d', depfile]
