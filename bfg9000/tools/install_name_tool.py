from . import tool
from .. import options as opts
from .common import darwin_install_name, SimpleCommand
from ..file_types import file_install_path
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


def post_install(env, options, output, *, is_library=False):
    change_opts = options.filter(opts.install_name_change)
    changes = ([(i.old, i.new) for i in change_opts] +
               [(darwin_install_name(i, env), file_install_path(i, cross=env))
                for i in output.runtime_deps])

    path = file_install_path(output)
    return env.tool('install_name_tool')(
        path, id=path.cross(env) if is_library else None, changes=changes
    )
