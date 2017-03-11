from . import tool
from .common import SimpleCommand


@tool('symlink')
class Symlink(SimpleCommand):
    rule_name = command_var = 'symlink'

    def __init__(self, env):
        # XXX: Support mklink?
        SimpleCommand.__init__(self, env, 'SYMLINK', 'ln -sf')

    def _call(self, cmd, input, output):
        return [cmd, input, output]
