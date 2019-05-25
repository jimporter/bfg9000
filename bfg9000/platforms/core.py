import platform
import re
import subprocess
import warnings
from collections import namedtuple
from pkg_resources import get_entry_info

from ..objutils import memoize
from ..versioning import SpecifierSet, Version

__all__ = ['known_platforms', 'parse_triplet', 'Platform', 'PlatformTriplet',
           'platform_name', 'platform_tuple']

# This lists the known platform families and genera.
known_platforms = ['posix', 'windows', 'linux', 'darwin', 'cygwin', 'winnt',
                   'win9x', 'msdos']
PlatformTriplet = namedtuple('PlatformTriplet', ['arch', 'vendor', 'sys',
                                                 'abi'])

_platform_genus = {
    'android': 'linux',
    'ios': 'darwin',
    'macos': 'darwin',
}

_triplet_abi = {'android', 'eabi', 'elf', 'gnu', 'macho'}


def parse_triplet(s, default_vendor='unknown'):
    def _result(arch, vendor_sys, abi=None):
        if len(vendor_sys) == 0:
            raise ValueError('expected <sys>')
        elif len(vendor_sys) == 1:
            return PlatformTriplet(arch, default_vendor, vendor_sys[0], abi)
        elif len(vendor_sys) == 2:
            return PlatformTriplet(arch, vendor_sys[0], vendor_sys[1], abi)
        raise ValueError('too many values')

    bits = s.split('-')
    if len(bits) < 2:
        raise ValueError('expected at least <arch>-<sys>')

    if bits[-1] in _triplet_abi:
        return _result(bits[0], bits[1:-1], bits[-1])
    return _result(bits[0], bits[1:], None)


# TODO: remove this after 0.4 is released.
class FancyString(str):
    _mapping = {
        'genus': {
            'windows': 'winnt',
        },
        'species': {
            'windows': 'winnt',
            'darwin': 'macos',
        },
    }

    def __eq__(self, rhs):
        if rhs in self._mapping:
            mapped = self._mapping[rhs]
            warnings.warn('{!r} is deprecated; use {!r} instead'
                          .format(rhs, mapped))
            return str.__eq__(self, mapped)
        return str.__eq__(self, rhs)

    def __hash__(self):  # pragma: no cover
        return str.__hash__(self)

    @classmethod
    def maybe_make(cls, value):
        if value in cls._mapping.values():
            return cls(value)
        return value


class FancyStringGenus(FancyString):
    _mapping = {
        'windows': 'winnt',
    }


class FancyStringSpecies(FancyString):
    _mapping = {
        'windows': 'winnt',
        'darwin': 'macos',
    }


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
            return 'winnt'
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
        return 'macos'

    # Not sure what this is...
    return system


def platform_tuple(name=None):
    # TODO: remove these after 0.4 is released.
    if name == 'windows':
        warnings.warn("'windows' is deprecated; use 'winnt' instead")
        name = 'winnt'
    elif name == 'darwin':
        warnings.warn("'darwin' is deprecated; use 'macos' instead")
        name = 'macos'
    elif name is None:
        name = platform_name()
    return _platform_genus.get(name, str(name)), name


class Platform(object):
    def __init__(self, genus, species, arch):
        self.genus = FancyStringGenus.maybe_make(genus)
        self.species = FancyStringSpecies.maybe_make(species)
        self.arch = arch

    @property
    def name(self):
        return self.species

    # TODO: remove this after 0.4 is released.
    @property
    def flavor(self):  # pragma: no cover
        warnings.warn('`flavor` is deprecated; use `family` instead')
        return self.family

    @property
    def _triplet_vendor(self):
        return 'pc' if re.match(r'i.86$', self.arch) else 'unknown'

    @property
    def triplet(self):
        return '{}-{}-{}'.format(self.arch, self._triplet_vendor,
                                 self._triplet_sys_abi)

    def to_json(self):
        return {
            'genus': self.genus,
            'species': self.species,
            'arch': self.arch,
        }

    def __eq__(self, rhs):
        return (self.genus == rhs.genus and self.species == rhs.species and
                self.arch == rhs.arch)

    def __ne__(self, rhs):
        return not self == rhs


@memoize
def _get_platform_info(kind, genus, species, arch):
    entry_point = 'bfg9000.platforms.{}'.format(kind)
    entry = get_entry_info('bfg9000', entry_point, genus)
    if entry is None:
        # Fall back to a generic POSIX system if we don't recognize the
        # platform name.
        entry = get_entry_info('bfg9000', entry_point, 'posix')
    return entry.load()(genus, species, arch)


def _platform_info(kind, name=None, arch=None):
    if name is None:
        name = platform_name()
    if arch is None:
        arch = platform.machine()
    genus, species = platform_tuple(name)
    return _get_platform_info(kind, genus, species, arch)
