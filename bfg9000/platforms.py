import platform
import re
import subprocess
from collections import namedtuple

def platform_name():
    name = platform.system().lower()
    if name == 'windows':
        try:
            name = subprocess.check_output('uname').rstrip().lower()
        except WindowsError:
            pass
    if name.startswith('cygwin'):
        return 'cygwin'
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
