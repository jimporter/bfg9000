from .hooks import tool
from .utils import check_which


@tool('doppel')
class Doppel(object):
    rule_name = command_var = 'doppel'

    def __init__(self, env):
        self.command = env.getvar('DOPPEL', 'doppel')
        check_which(self.command)

    @property
    def data_args(self):
        return ['-m', '644']

    def __call__(self, cmd, src, dst):
        return [cmd, '-p', src, dst]
