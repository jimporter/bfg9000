from . import tool

@tool('mkdir_p')
class MkdirP(object):
    rule_name = command_var = 'mkdir_p'

    def __init__(self, env):
        default = 'gmkdir' if env.platform.name == 'windows' else 'mkdir'
        self.command = env.getvar('MKDIR_P', default + ' -p')

    def __call__(self, cmd, path):
        return [cmd, path]

    # XXX: Remove this once we rewrite the install command.
    def copy(self, cmd, src, dst):
        return cmd + ' ' + dst + ' && cp -r ' + src + '/* ' + dst
