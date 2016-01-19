import os
import platform
import subprocess

from .iterutils import iterate
from .path import Path, Root, InstallRoot


def platform_name():
    name = platform.system().lower()
    if name == 'windows':
        try:
            uname = subprocess.check_output(
                'uname', universal_newlines=True
            ).lower()
            if uname.startswith('cygwin'):
                name = 'cygwin'
        except WindowsError:
            pass
    return name


# XXX: How much information should be stored in Platforms vs the Environment?
# For instance, should the Platforms know how to fetch platform-specific
# environment variables (implying a circular dependency between Environment and
# Platform), or should it just hand off the var name to the Environment?
class Platform(object):
    def __init__(self, name):
        self.name = name


class PosixPlatform(Platform):
    @property
    def flavor(self):
        return 'posix'

    @property
    def executable_ext(self):
        return ''

    @property
    def shared_library_ext(self):
        return '.so'

    @property
    def has_import_library(self):
        return False

    @property
    def has_rpath(self):
        return False

    @property
    def include_dirs(self):
        return ['/usr/local/include', '/usr/include']

    @property
    def lib_dirs(self):
        return ['/usr/local/lib', '/lib', '/usr/lib']

    @property
    def install_dirs(self):
        return {
            InstallRoot.prefix:     Path('/usr/local', Root.absolute),
            InstallRoot.bindir:     Path('bin', InstallRoot.prefix),
            InstallRoot.libdir:     Path('lib', InstallRoot.prefix),
            InstallRoot.includedir: Path('include', InstallRoot.prefix),
        }


class LinuxPlatform(PosixPlatform):
    @property
    def has_rpath(self):
        return True


class DarwinPlatform(PosixPlatform):
    @property
    def shared_library_ext(self):
        return '.dylib'


class WindowsPlatform(Platform):
    @property
    def flavor(self):
        return 'windows'

    @property
    def executable_ext(self):
        return '.exe'

    @property
    def shared_library_ext(self):
        return '.dll'

    @property
    def has_import_library(self):
        return True

    @property
    def has_rpath(self):
        return False

    @property
    def include_dirs(self):
        # TODO: Provide a list of include paths
        return []

    @property
    def lib_dirs(self):
        # TODO: Provide a list of lib paths
        return []

    @property
    def install_dirs(self):
        return {
            # TODO: Pick a better prefix
            InstallRoot.prefix:     Path('C:\\', Root.absolute),
            InstallRoot.bindir:     Path('', InstallRoot.prefix),
            InstallRoot.libdir:     Path('', InstallRoot.prefix),
            InstallRoot.includedir: Path('', InstallRoot.prefix),
        }


class CygwinPlatform(WindowsPlatform):
    @property
    def flavor(self):
        return 'posix'


def platform_info(name=None):
    if name is None:
        name = platform_name()

    if name == 'windows':
        return WindowsPlatform(name)
    elif name == 'cygwin':
        return CygwinPlatform(name)
    elif name == 'darwin':
        return DarwinPlatform(name)
    elif name == 'linux':
        return LinuxPlatform(name)
    else:  # Probably some POSIX system
        return PosixPlatform(name)


def which(names, env=os.environ):
    # XXX: Create something to manage host-platform stuff like this?
    # (`Platform` is for targets.)
    paths = env.get('PATH', os.defpath).split(os.pathsep)
    if platform_name() in ['windows', 'cygwin']:
        exts = env.get('PATHEXT', '').split(os.pathsep)
    else:
        exts = ['']

    for name in iterate(names):
        if os.path.isabs(name):
            if os.path.exists(name):
                return name
        else:
            for path in ['.'] if os.path.dirname(name) else paths:
                for ext in exts:
                    fullpath = os.path.normpath(os.path.join(path, name + ext))
                    if os.path.exists(fullpath):
                        return fullpath

    raise IOError("unable to find executable '{}'".format(name))
