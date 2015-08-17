from .. import safe_str
from ..file_types import SharedLibrary
from ..iterutils import uniques
from ..path import install_path

class PatchElf(object):
    def __init__(self, env):
        self.command_name = env.getvar('PATCHELF', 'patchelf')
        self.command_var = 'patchelf'

    def command(self, cmd, file):
        paths = uniques(
                install_path(i.path, i.install_root).parent()
                for i in file.creator.libs if isinstance(i, SharedLibrary)
        )
        if paths:
            return [cmd, '--set-rpath', safe_str.join(paths, ':'),
                    install_path(file.path, file.install_root)]
