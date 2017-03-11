from . import tool
from .common import SimpleCommand
from ..iterutils import listify


@tool('install_name_tool')
class InstallNameTool(SimpleCommand):
    rule_name = command_var = 'install_name_tool'

    def __init__(self, env):
        SimpleCommand.__init__(
            self, env, name='install_name_tool', env_var='INSTALL_NAME_TOOL',
            default='install_name_tool'
        )

    def _call(self, cmd, file, id=None, delete_rpath=None, changes=[]):
        rpath = getattr(file, 'darwin_rpath', None)

        args = []
        if id:
            args += ['-id', id]
        if rpath:
            args += ['-delete_rpath', rpath]
        args = sum((['-change'] + listify(i) for i in changes), args)

        if args:
            return [cmd] + args + [file]
