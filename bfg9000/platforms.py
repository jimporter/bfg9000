import platform
import subprocess
from collections import namedtuple

def platform_name():
    name = platform.system().lower()
    if name == 'windows':
        try:
            name = subprocess.check_output('uname').rstrip().lower()
        except subprocess.CalledProcessError:
            pass
    if name.startswith('cygwin'):
        return 'cygwin'
    return name

PlatformInfo = namedtuple('PlatformInfo', [
    'name', 'executable_ext', 'shared_library_ext', 'has_import_library',
    'has_rpath'
])

def platform_info(name):
    # TODO: This should probably be made more flexible somehow...
    if name == 'windows' or name == 'cygwin':
        return PlatformInfo(name, '.exe', '.dll', True, False)
    elif name == 'darwin':
        return PlatformInfo(name, '', '.dylib', False, False)
    else: # Probably some POSIX system
        return PlatformInfo(name, '', '.so', False, True)
