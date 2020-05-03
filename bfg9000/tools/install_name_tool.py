from . import tool
from .common import SimpleCommand
from ..iterutils import flatten, listify


@tool('install_name_tool')
class InstallNameTool(SimpleCommand):
    rule_name = command_var = 'install_name_tool'

    def __init__(self, env):
        super().__init__(
            env, name='install_name_tool', env_var='INSTALL_NAME_TOOL',
            default='install_name_tool'
        )

    def _call(self, cmd, file, *, id=None, changes=[]):
        args = []
        if id:
            args += ['-id', id]
        args += flatten(['-change'] + listify(i) for i in changes)

        if args:
            return cmd + args + [file]
