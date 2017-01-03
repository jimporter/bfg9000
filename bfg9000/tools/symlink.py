from .hooks import tool
from .utils import SimpleCommand


@tool('symlink')
class Symlink(SimpleCommand):
    rule_name = command_var = 'symlink'

    def __init__(self, env):
        # XXX: Support mklink?
        SimpleCommand.__init__(self, env, 'SYMLINK', 'ln -sf')

    def __call__(self, cmd, input, output):
        return [cmd, input, output]
