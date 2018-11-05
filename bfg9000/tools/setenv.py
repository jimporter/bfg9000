from . import tool
from .common import SimpleCommand
from ..platforms.host import platform_info
from ..safe_str import jbos, safe_str, shell_literal
from ..shell import escape_line


if platform_info().family == 'windows':
    @tool('setenv')
    class SetEnv(SimpleCommand):
        def __init__(self, env):
            SimpleCommand.__init__(self, env, name='setenv', env_var='SETENV',
                                   default=env.bfgdir.append('pysetenv'))

        def _call(self, cmd, env, line):
            if env:
                eq = shell_literal('=')
                env_vars = cmd + [jbos(safe_str(name), eq, safe_str(value))
                                  for name, value in env.iteritems()] + ['--']
            else:
                env_vars = []
            return env_vars + escape_line(line, listify=True)
