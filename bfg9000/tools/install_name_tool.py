import os

from . import tool
from .. import file_types, options as opts
from .common import SimpleCommand
from ..iterutils import flatten
from ..path import BasePath, Path, Root, InstallRoot


@tool('install_name_tool')
class InstallNameTool(SimpleCommand):
    rule_name = command_var = 'install_name_tool'

    def __init__(self, env):
        super().__init__(
            env, name='install_name_tool', env_var='INSTALL_NAME_TOOL',
            default='install_name_tool'
        )

    def _call(self, cmd, file, *, id=None, changes=[], rpaths=[]):
        args = []
        if id:
            args += ['-id', id]
        args += flatten(['-change', old, new] for old, new in changes)
        for old, new in rpaths:
            if old and new:
                args += ['-rpath', old, new]
            elif new:
                args += ['-add_rpath', new]
            elif old:
                args += ['-delete_rpath', old]

        if args:
            return cmd + args + [file]


def install_name(env, library, *, strict=True):
    if library.runtime_file:
        path = library.runtime_file.path
        if path.root in InstallRoot:
            return path.cross(env)
        else:
            return os.path.join('@rpath', path.suffix)
    elif not strict:
        return None

    raise TypeError('unable to create install_name')  # pragma: no cover


def local_rpath(env, library, output):
    if not library.runtime_file:
        return None

    rpath = library.runtime_file.path.parent().cross(env)
    if rpath.root != Root.absolute and rpath.root not in InstallRoot:
        if not output:
            raise ValueError('unable to construct runtime search path')
        # This should almost always be true, except for when linking to a
        # shared library stored in the srcdir.
        if rpath.root == output.path.root:
            rpath = Path('.', rpath.root).relpath(output.path.parent(),
                                                  prefix='@loader_path')
    return rpath


def installed_rpath(env, library, install_db):
    if not library.runtime_file:
        return None
    try:
        return install_db.target[library.runtime_file].path.parent()
    except KeyError:
        if library.runtime_file.path.root == Root.absolute:
            return library.runtime_file.path.parent()
        raise


def post_install(env, options, output, install_db, *, is_library=False):
    new_id = None
    if is_library:
        installed_id = install_name(env, install_db.host[output])
        if installed_id != install_name(env, output):
            new_id = installed_id

    change_opts = options.filter(opts.install_name_change)
    changes = ([(i.old, i.new) for i in change_opts] +
               [(install_name(env, i), install_name(env, install_db.target[i]))
                for i in output.runtime_deps])

    # Compute all the changed rpaths, preserving the original order. To do
    # this, add all the entries into a dict with the key being the old rpath;
    # for new entries, set the key to a sentinel value for uniqueness, which
    # we'll remove at the end.
    new_rpaths = {}
    sentinel = 1
    for i in options:
        if isinstance(i, opts.lib):
            if not isinstance(i.library, file_types.Library):
                continue
            local = local_rpath(env, i.library, output)
            if local is not None:
                installed = installed_rpath(env, i.library, install_db)
                if not isinstance(local, BasePath) or local != installed:
                    new_rpaths[local] = installed
        elif isinstance(i, opts.rpath_dir):
            if i.when == opts.RpathWhen.installed:
                new_rpaths[sentinel] = i.path
                sentinel += 1
            elif i.when == opts.RpathWhen.uninstalled:
                new_rpaths[i.path] = None
    new_rpaths = ((k if not isinstance(k, int) else None, v)
                  for k, v in new_rpaths.items())

    path = install_db.host[output].path
    return env.tool('install_name_tool')(
        path, id=new_id, changes=changes, rpaths=new_rpaths
    )
