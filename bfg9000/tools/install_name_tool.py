from . import tool
from .. import file_types, options as opts
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


def darwin_install_name(library, env, strict=True):
    while isinstance(library, file_types.LinkLibrary):
        library = library.library

    if isinstance(library, file_types.VersionedSharedLibrary):
        return library.soname.path.string(env.base_dirs)
    elif isinstance(library, file_types.SharedLibrary):
        return library.path.string(env.base_dirs)
    elif strict:  # pragma: no cover
        raise TypeError('unable to create darwin install_name')
    else:
        return None


def post_install(env, options, output, install_db, *, is_library=False):
    change_opts = options.filter(opts.install_name_change)
    changes = ([(i.old, i.new) for i in change_opts] +
               [(darwin_install_name(i, env), install_db.target[i].path)
                for i in output.runtime_deps])

    path = install_db.host[output].path
    return env.tool('install_name_tool')(
        path, id=path.cross(env) if is_library else None, changes=changes
    )
