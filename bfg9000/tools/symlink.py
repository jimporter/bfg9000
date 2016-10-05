from .hooks import tool
from .utils import check_which


@tool('symlink')
class Symlink(object):
    rule_name = command_var = 'symlink'

    def __init__(self, env):
        # XXX: Support mklink?
        self.command = env.getvar('SYMLINK', 'ln -sf')
        check_which(self.command)

    def __call__(self, cmd, input, output):
        return [cmd, input, output]
