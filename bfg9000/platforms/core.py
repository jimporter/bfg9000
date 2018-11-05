import platform
import re
import subprocess
import warnings
from collections import namedtuple
from pkg_resources import get_entry_info, DistributionNotFound

from ..objutils import memoize
from ..versioning import SpecifierSet, Version

__all__ = ['known_platforms', 'PathTraits', 'Platform', 'platform_name',
           'platform_tuple']

# This lists the known platform families and genera.
known_platforms = ['posix', 'windows', 'linux', 'darwin', 'cygwin', 'winnt',
                   'win9x', 'msdos']
PathTraits = namedtuple('PathTraits', ['curdir', 'pathsep'])

_platform_genus = {
    'android': 'linux',
    'ios': 'darwin',
    'macos': 'darwin',
}


# TODO: remove this after 0.4 is released.
class FancyString(str):
    def __eq__(self, rhs):
        if rhs == 'windows':
            warnings.warn("'windows' is deprecated; use 'winnt' instead")
            return str.__eq__(self, 'winnt')
        if rhs == 'darwin':
            warnings.warn("'darwin' is deprecated; use 'macos' instead")
            return str.__eq__(self, 'macos')
        return str.__eq__(self, rhs)

    def __hash__(self):
        return str.__hash__(self)


@memoize
def platform_name():
    system = platform.system().lower()
    if system.startswith('cygwin'):
        return 'cygwin'

    if system == 'windows':
        try:
            uname = subprocess.check_output(
                'uname', universal_newlines=True
            ).lower()
            if uname.startswith('cygwin'):
                return 'cygwin'
        except OSError:
            pass

        version = Version(platform.version())
        if version not in SpecifierSet('!=3.10.528,!=3.50.807,!=3.51.1057,' +
                                       '!=4.00.1381,<5'):
            return FancyString('winnt')
        elif version in SpecifierSet('>=4'):
            return 'win9x'
        return 'msdos'
    elif system == 'linux':
        try:
            distro = subprocess.check_output(
                ['lsb_release', '-is'], universal_newlines=True
            ).lower()
            if distro == 'android':
                return 'android'
        except OSError:
            pass
        return system
    elif system == 'darwin':
        machine = platform.machine()
        if re.match(r'(iPhone|iPad|iPod)', machine):
            return 'ios'
        return FancyString('macos')

    # Not sure what this is...
    return system


def platform_tuple(name=None):
    # TODO: remove these after 0.4 is released.
    if str(name) == 'windows':
        warnings.warn("'windows' is deprecated; use 'winnt' instead")
        name = FancyString('winnt')
    elif str(name) == 'darwin':
        warnings.warn("'darwin' is deprecated; use 'macos' instead")
        name = FancyString('macos')
    elif name is None:
        name = platform_name()
    return _platform_genus.get(name, str(name)), name


class Platform(object):
    def __init__(self, genus, species):
        self.genus = genus
        self.species = species

    @property
    def name(self):
        return self.species

    # TODO: remove this after 0.4 is released.
    @property
    def flavor(self):  # pragma: no cover
        warnings.warn('`flavor` is deprecated; use `family` instead')
        return self.family


@memoize
def _get_platform_info(name, kind):
    genus, species = platform_tuple(name)
    entry_point = 'bfg9000.platforms.{}'.format(kind)
    entry = get_entry_info('bfg9000', entry_point, genus)
    if entry is None:
        # Fall back to a generic POSIX system if we don't recognize the
        # platform name.
        entry = get_entry_info('bfg9000', entry_point, 'posix')
    return entry.load()(genus, species)
