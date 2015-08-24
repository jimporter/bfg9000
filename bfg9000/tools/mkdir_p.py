from . import tool

@tool('mkdir_p')
class MkdirP(object):
    def __init__(self, env):
        default = 'gmkdir' if env.platform.name == 'windows' else 'mkdir'
        self.command_name = env.getvar('MKDIR_P', default + ' -p')
        self.command_var = 'mkdir_p'

    def command(self, cmd, path):
        return [cmd, path]

    # TODO: Remove this once we rewrite the install command.
    def copy_command(self, cmd, src, dst):
        return cmd + ' ' + dst + ' && cp -r ' + src + '/* ' + dst
