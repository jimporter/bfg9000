import os
import platform
import subprocess

from .iterutils import iterate
from .path import Path, Root, InstallRoot

known_platforms = ['posix', 'linux', 'darwin', 'cygwin', 'windows']


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


# Platform objects are primarily intended to represent information about the
# target platform for a build. Currently, we store some source platform
# information here as well (e.g. include/library dirs). In the future, when we
# support cross-compilation, stuff like that should be moved elsewhere.
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
    def has_versioned_library(self):
        return True

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
    def object_format(self):
        return 'elf'

    @property
    def has_rpath(self):
        return True


class DarwinPlatform(PosixPlatform):
    @property
    def object_format(self):
        return 'mach-o'

    @property
    def shared_library_ext(self):
        return '.dylib'

    @property
    def has_rpath(self):
        return True


class WindowsPlatform(Platform):
    @property
    def flavor(self):
        return 'windows'

    @property
    def object_format(self):
        return 'coff'

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
    def has_versioned_library(self):
        return False

    @property
    def has_rpath(self):
        return False

    @property
    def include_dirs(self):
        # Windows doesn't have standard include dirs; for MSVC, this will get
        # pulled in from the $INCLUDE environment variable.
        return []

    @property
    def lib_dirs(self):
        # Windows doesn't have standard library dirs; for MSVC, this will get
        # pulled in from the $LIB environment variable.
        return []

    @property
    def install_dirs(self):
        return {
            # XXX: Pick a better prefix. Maybe install to C:\<project-name>?
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
