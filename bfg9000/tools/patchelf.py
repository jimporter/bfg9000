from . import tool
from .. import options as opts, safe_str
from .common import SimpleCommand
from ..file_types import file_install_path, Library
from ..iterutils import uniques
from ..path import BasePath, InstallRoot, Root


@tool('patchelf')
class PatchElf(SimpleCommand):
    def __init__(self, env):
        super().__init__(env, name='patchelf', env_var='PATCHELF',
                         default='patchelf')

    def _call(self, cmd, file, rpath=None):
        if rpath:
            return cmd + ['--set-rpath', safe_str.join(rpath, ':'), file]


def local_rpath(env, library, output):
    if not library.runtime_file:
        return None

    rpath = library.runtime_file.path.parent().cross(env)
    if rpath.root != Root.absolute and rpath.root not in InstallRoot:
        if not output:
            raise ValueError('unable to construct rpath')
        # This should almost always be true, except for when linking to a
        # shared library stored in the srcdir.
        if rpath.root == output.path.root:
            rpath = rpath.relpath(output.path.parent(), prefix='$ORIGIN')
    return rpath


def installed_rpath(env, library):
    if not library.runtime_file:
        return None
    return file_install_path(library.runtime_file, cross=env).parent()


def post_install(env, options, output):
    rpaths = []
    changed = False
    for i in options:
        if isinstance(i, opts.lib):
            if not isinstance(i.library, Library):
                continue
            local = local_rpath(env, i.library, output)
            if local is not None:
                installed = installed_rpath(env, i.library)
                rpaths.append(installed)
                if not isinstance(local, BasePath) or local != installed:
                    changed = True
        elif isinstance(i, opts.rpath_dir):
            if i.when & opts.RpathWhen.installed:
                if not (i.when & opts.RpathWhen.uninstalled):
                    changed = True
                rpaths.append(i.path)

    rpaths = uniques(rpaths) if changed else []
    return env.tool('patchelf')(file_install_path(output), rpaths)
