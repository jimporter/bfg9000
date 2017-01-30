from .hooks import tool
from .utils import darwin_install_name, SimpleCommand
from ..path import install_path


@tool('install_name_tool')
class InstallNameTool(SimpleCommand):
    rule_name = command_var = 'install_name_tool'

    def __init__(self, env):
        SimpleCommand.__init__(self, env, 'INSTALL_NAME_TOOL',
                               'install_name_tool')

    def __call__(self, cmd, file, libraries):
        # XXX: Delete the rpath for `file` too?
        def change(lib):
            return ['-change', darwin_install_name(lib),
                    install_path(lib.path, lib.install_root)]
        args = sum((change(i) for i in libraries), [])

        if args:
            path = install_path(file.path, file.install_root)
            return [cmd] + args + [path]
