from .. import safe_str
from .hooks import tool
from .utils import SimpleCommand
from ..iterutils import uniques
from ..path import install_path


@tool('patchelf')
class PatchElf(SimpleCommand):
    rule_name = command_var = 'patchelf'

    def __init__(self, env):
        SimpleCommand.__init__(self, env, 'PATCHELF', 'patchelf')

    def __call__(self, cmd, file, libraries):
        paths = uniques(install_path(i.path, i.install_root).parent()
                        for i in libraries)
        if paths:
            return [cmd, '--set-rpath', safe_str.join(paths, ':'),
                    install_path(file.path, file.install_root)]
