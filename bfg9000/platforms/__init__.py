import platform
import subprocess
from pkg_resources import get_entry_info, DistributionNotFound

known_platforms = ['posix', 'linux', 'darwin', 'cygwin', 'windows']
_platform_name = None
_platform_info = {}


# Platform objects are primarily intended to represent information about the
# target platform for a build. Currently, we store some source platform
# information here as well (e.g. include/library dirs). In the future, when we
# support cross-compilation, stuff like that should be moved elsewhere.
class Platform(object):
    _package_map = {}

    def __init__(self, name):
        self.name = name

    def transform_package(self, name):
        return self._package_map.get(name, name)


def platform_name():
    global _platform_name
    if _platform_name is None:
        _platform_name = platform.system().lower()
        if _platform_name == 'windows':
            try:
                uname = subprocess.check_output(
                    'uname', universal_newlines=True
                ).lower()
                if uname.startswith('cygwin'):
                    _platform_name = 'cygwin'
            except WindowsError:
                pass
    return _platform_name


def platform_info(name=None):
    if name is None:
        name = platform_name()
    if name in _platform_info:
        return _platform_info[name]

    entry = get_entry_info('bfg9000', 'bfg9000.platforms', name)
    if entry is None:
        # Fall back to a generic POSIX system if we don't recognize the
        # platform name.
        entry = get_entry_info('bfg9000', 'bfg9000.platforms', 'posix')

    result = _platform_info[name] = entry.load()(name)
    return result
