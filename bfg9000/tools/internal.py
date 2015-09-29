import os.path

from . import tool
from ..platforms import platform_name

@tool('bfg9000')
class Bfg9000(object):
    def __init__(self, env):
        self.name = self.command_var = 'bfg9000'
        self.command_name = env.getvar('BFG9000', env.bfgpath)

@tool('depfixer')
class Depfixer(object):
    def __init__(self, env):
        self.name = self.command_var = 'depfixer'
        default = os.path.join(os.path.dirname(env.bfgpath), 'bfg9000-depfixer')
        self.command_name = env.getvar('DEPFIXER', default)

if platform_name() == 'windows':
    @tool('setenv')
    class SetEnv(object):
        def __init__(self, env):
            self.name = self.command_var = 'setenv'
            default = os.path.join(os.path.dirname(env.bfgpath),
                                   'bfg9000-setenv')
            self.command_name = env.getvar('SETENV', default)
