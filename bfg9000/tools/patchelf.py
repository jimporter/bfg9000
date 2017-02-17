from . import tool
from .. import safe_str
from .utils import SimpleCommand


@tool('patchelf')
class PatchElf(SimpleCommand):
    rule_name = command_var = 'patchelf'

    def __init__(self, env):
        SimpleCommand.__init__(self, env, 'PATCHELF', 'patchelf')

    def _call(self, cmd, file, rpath=None):
        if rpath:
            return [cmd, '--set-rpath', safe_str.join(rpath, ':'), file]
