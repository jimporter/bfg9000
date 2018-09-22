import platform
import subprocess
from collections import namedtuple
from pkg_resources import get_entry_info, DistributionNotFound

from ..objutils import memoize

__all__ = ['known_platforms', 'PathTraits', 'Platform', 'platform_name']

known_platforms = ['posix', 'linux', 'darwin', 'cygwin', 'windows']
PathTraits = namedtuple('PathTraits', ['curdir', 'pathsep'])


@memoize
def platform_name():
    platform_name = platform.system().lower()
    if platform_name.startswith('cygwin'):
        return 'cygwin'

    if platform_name == 'windows':
        try:
            uname = subprocess.check_output(
                'uname', universal_newlines=True
            ).lower()
            if uname.startswith('cygwin'):
                return 'cygwin'
        except OSError:
            pass

    return platform_name


class Platform(object):
    def __init__(self, name):
        self.name = name


@memoize
def _get_platform_info(name, kind):
    entry_point = 'bfg9000.platforms.{}'.format(kind)
    entry = get_entry_info('bfg9000', entry_point, name)
    if entry is None:
        # Fall back to a generic POSIX system if we don't recognize the
        # platform name.
        entry = get_entry_info('bfg9000', entry_point, 'posix')
    return entry.load()(name)
