from .hooks import tool
from .utils import check_which


@tool('mkdir_p')
class MkdirP(object):
    rule_name = command_var = 'mkdir_p'

    def __init__(self, env):
        default = 'doppel -p' if env.platform.name == 'windows' else 'mkdir -p'
        self.command = env.getvar('MKDIR_P', default)
        check_which(self.command)

    def __call__(self, cmd, path):
        return [cmd, path]
