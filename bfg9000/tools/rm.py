from itertools import chain

from . import tool
from .common import SimpleCommand
from ..iterutils import iterate


@tool('rm')
class Rm(SimpleCommand):
    def __init__(self, env):
        default = ['rm -f']
        if env.host_platform.family == 'windows':
            default.append('cmd /c del')
        SimpleCommand.__init__(self, env, name='rm', env_var='RM',
                               default=default)

    def _call(self, cmd, files):
        return list(chain(cmd, iterate(files)))
