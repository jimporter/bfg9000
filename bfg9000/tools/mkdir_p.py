from . import tool
from .common import SimpleCommand


@tool('mkdir_p')
class MkdirP(SimpleCommand):
    def __init__(self, env):
        default = ('doppel -p' if env.host_platform.family == 'windows'
                   else 'mkdir -p')
        SimpleCommand.__init__(self, env, name='mkdir_p', env_var='MKDIR_P',
                               default=default)

    def _call(self, cmd, path):
        return cmd + [path]
