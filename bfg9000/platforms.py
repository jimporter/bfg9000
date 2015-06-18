import platform
import re
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
    'has_rpath', 'lib_paths'
])

def platform_info(name):
    # TODO: This should probably be made more flexible somehow...
    # Also, come up with a better list of lib paths for the various platforms.
    if name == 'windows' or name == 'cygwin':
        return PlatformInfo(name, '.exe', '.dll', True, False, [])
    elif name == 'darwin':
        return PlatformInfo(name, '', '.dylib', False, False, ['/usr/lib'])
    else: # Probably some POSIX system
        try:
            # XXX: This probably won't work very well for cross-compilation.
            output = subprocess.check_output(['ld', '--verbose'])
            paths = re.findall(r'SEARCH_DIR\("=?(.*?)"\);', output)
        except:
            paths = ['/usr/local/lib', '/lib', '/usr/lib']
        return PlatformInfo(name, '', '.so', False, True, paths)
