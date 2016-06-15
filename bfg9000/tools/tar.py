from .hooks import tool
from .utils import check_which

from ..iterutils import iterate


@tool('tar')
class Tar(object):
    rule_name = command_var = 'tar'

    def __init__(self, env):
        self.command = env.getvar('TAR', 'tar')
        check_which(self.command)

    def __call__(self, cmd, src, dst, base=None, recurse=True):
        result = [cmd, '-czf', dst]
        if not recurse:
            result.append('--no-recursion')
        if base:
            result.extend(['-C', base])
        result.extend(iterate(src))
        return result
