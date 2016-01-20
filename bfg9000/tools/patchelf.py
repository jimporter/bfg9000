from .. import safe_str
from .hooks import tool
from ..file_types import SharedLibrary
from ..iterutils import uniques
from ..path import install_path


@tool('patchelf')
class PatchElf(object):
    rule_name = command_var = 'patchelf'

    def __init__(self, env):
        self.command = env.getvar('PATCHELF', 'patchelf')

    def __call__(self, cmd, file):
        paths = uniques(
            install_path(i.path, i.install_root).parent()
            for i in file.creator.all_libs if isinstance(i, SharedLibrary)
        )
        if paths:
            return [cmd, '--set-rpath', safe_str.join(paths, ':'),
                    install_path(file.path, file.install_root)]
