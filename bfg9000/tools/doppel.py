from .hooks import tool
from .utils import check_which

from ..iterutils import iterate


@tool('doppel')
class Doppel(object):
    rule_name = command_var = 'doppel'

    def __init__(self, env):
        self.command = env.getvar('DOPPEL', 'doppel')
        check_which(self.command)

    @property
    def data_args(self):
        return ['-m', '644']

    def copy_onto(self, cmd, src, dst):
        return [cmd, '-p', src, dst]

    def copy_into(self, cmd, src, dst, base=None):
        result = [cmd, '-ipN']
        if base:
            result.extend(['-C', base])
        result.extend(iterate(src))
        result.append(dst)
        return result
