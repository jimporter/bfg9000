from . import tool
from .utils import SimpleCommand


@tool('mkdir_p')
class MkdirP(SimpleCommand):
    rule_name = command_var = 'mkdir_p'

    def __init__(self, env):
        default = 'doppel -p' if env.platform.name == 'windows' else 'mkdir -p'
        SimpleCommand.__init__(self, env, 'MKDIR_P', default)

    def _call(self, cmd, path):
        return [cmd, path]
