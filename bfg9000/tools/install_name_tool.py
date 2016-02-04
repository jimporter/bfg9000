from .hooks import tool
from .utils import check_which, darwin_install_name
from ..path import install_path


@tool('install_name_tool')
class InstallNameTool(object):
    rule_name = command_var = 'install_name_tool'

    def __init__(self, env):
        self.command = env.getvar('INSTALL_NAME_TOOL', 'install_name_tool')
        check_which(self.command)

    def __call__(self, cmd, file, libraries):
        def change(lib):
            return ['-change', darwin_install_name(lib),
                    install_path(lib.path, lib.install_root)]
        args = sum((change(i) for i in libraries), [])

        if args:
            path = install_path(file.path, file.install_root)
            return [cmd] + args + [path]
