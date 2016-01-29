from .hooks import tool
from .utils import check_which


@tool('mkdir_p')
class MkdirP(object):
    rule_name = command_var = 'mkdir_p'

    def __init__(self, env):
        if env.platform.name == 'windows':
            default = env.bfgpath.parent().append('bfg9000-makedirs')
        else:
            default = 'mkdir -p'
        self.command = env.getvar('MKDIR_P', default)
        check_which(self.command)

    def __call__(self, cmd, path):
        return [cmd, path]

    # XXX: Remove this once we rewrite the install command.
    def copy(self, cmd, src, dst):
        return cmd + ' ' + dst + ' && cp -r ' + src + '/* ' + dst
