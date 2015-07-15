import platform
import re
import subprocess
from collections import namedtuple

from path import Path

def platform_name():
    name = platform.system().lower()
    if name == 'windows':
        try:
            uname = subprocess.check_output('uname').rstrip().lower()
            if uname.startswith('cygwin'):
                name = 'cygwin'
        except WindowsError:
            pass
    return name

class Platform(object):
    def __init__(self, name):
        self.name = name

class PosixPlatform(Platform):
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
    def lib_dirs(self):
        return ['/usr/local/lib', '/lib', '/usr/lib']

    @property
    def install_dirs(self):
        return {
            Path.prefix:     Path('/usr/local', Path.absolute),
            Path.bindir:     Path('bin', Path.prefix),
            Path.libdir:     Path('lib', Path.prefix),
            Path.includedir: Path('include', Path.prefix),
        }

class LinuxPlatform(PosixPlatform):
    @property
    def has_rpath(self):
        return True

    @property
    def lib_dirs(self):
        try:
            # XXX: This probably won't work very well for cross-compilation.
            output = subprocess.check_output(['ld', '--verbose'])
            paths = re.findall(r'SEARCH_DIR\("=?(.*?)"\);', output)
            if paths:
                return paths
        except:
            pass
        return PosixPlatform.lib_dirs(self)

class DarwinPlatform(PosixPlatform):
    @property
    def shared_library_ext(self):
        return '.dylib'

class WindowsPlatform(Platform):
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
    def lib_dirs(self):
        # TODO: Provide a list of lib paths
        return []

    @property
    def install_dirs(self):
        return {
            # TODO: Pick a better prefix
            Path.prefix:     Path('C:\\', Path.absolute),
            Path.bindir:     Path('', Path.prefix),
            Path.libdir:     Path('', Path.prefix),
            Path.includedir: Path('', Path.prefix),
        }

def platform_info(name=None):
    if name is None:
        name = platform_name()

    if name == 'windows' or name == 'cygwin':
        return WindowsPlatform(name)
    elif name == 'darwin':
        return DarwinPlatform(name)
    elif name == 'linux':
        return LinuxPlatform(name)
    else: # Probably some POSIX system
        return PosixPlatform(name)
