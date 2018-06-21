from . import tool
from .common import SimpleCommand
from .. import safe_str


@tool('patchelf')
class PatchElf(SimpleCommand):
    def __init__(self, env):
        SimpleCommand.__init__(self, env, name='patchelf', env_var='PATCHELF',
                               default='patchelf')

    def _call(self, cmd, file, rpath=None):
        if rpath:
            return cmd + ['--set-rpath', safe_str.join(rpath, ':'), file]
