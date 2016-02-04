from .. import safe_str
from .hooks import tool
from .utils import check_which
from ..iterutils import uniques
from ..path import install_path


@tool('patchelf')
class PatchElf(object):
    rule_name = command_var = 'patchelf'

    def __init__(self, env):
        self.command = env.getvar('PATCHELF', 'patchelf')
        check_which(self.command)

    def __call__(self, cmd, file, libraries):
        paths = uniques(install_path(i.path, i.install_root).parent()
                        for i in libraries)
        if paths:
            return [cmd, '--set-rpath', safe_str.join(paths, ':'),
                    install_path(file.path, file.install_root)]
