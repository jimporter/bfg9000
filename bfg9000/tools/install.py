from .. import safe_str
from ..file_types import SharedLibrary
from ..iterutils import uniques
from ..path import install_path

class Install(object):
    def __init__(self, env):
        self.command_name = env.getvar('INSTALL', 'install')
        self.command_var = 'install'

    @property
    def data_args(self):
        return ['-m', '644']

    def command(self, cmd, src, dst):
        return [cmd, '-D', src, dst]
