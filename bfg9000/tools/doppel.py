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

    def copy_into(self, cmd, src, dst, directory=None):
        result = [cmd, '-ipN']
        if directory:
            result.extend(['-C', directory])
        result.extend(iterate(src))
        result.append(dst)
        return result

    def archive(self, cmd, format, src, dst, directory=None, dest_prefix=None):
        result = [cmd, '-ipN', '-f', format]
        if directory:
            result.extend(['-C', directory])
        if dest_prefix:
            result.extend(['-P', dest_prefix])
        result.extend(iterate(src))
        result.append(dst)
        return result
