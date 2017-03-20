from . import tool
from .common import SimpleCommand


@tool('symlink')
class Symlink(SimpleCommand):
    def __init__(self, env):
        # This only supports `ln`, not `mklink`, since only administrators can
        # symlink with `mklink` by default. Windows sure is weird!
        SimpleCommand.__init__(self, env, name='symlink', env_var='SYMLINK',
                               default='ln -sf')

    def _call(self, cmd, input, output):
        return cmd + [input, output]
