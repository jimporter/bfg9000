import importlib_metadata as metadata
import os
import platform
import re
import subprocess
from collections import namedtuple

from ..objutils import memoize
from ..versioning import SpecifierSet, Version

__all__ = ['known_native_object_formats', 'known_platforms', 'parse_triplet',
           'Platform', 'PlatformTriplet', 'platform_name', 'platform_tuple']

# This lists the known platform families and genera.
known_platforms = ['posix', 'windows', 'linux', 'darwin', 'cygwin', 'winnt',
                   'win9x', 'msdos']
# This lists the known native object formats.
known_native_object_formats = ['elf', 'mach-o', 'coff']

PlatformTriplet = namedtuple('PlatformTriplet', ['arch', 'vendor', 'sys',
                                                 'abi'])

_platform_genus = {
    'android': 'linux',
    'ios': 'darwin',
    'macos': 'darwin',
}

_triplet_abi = {'android', 'eabi', 'elf', 'gnu', 'macho'}

_non_winnt_versions = SpecifierSet('!=3.10.528,!=3.50.807,!=3.51.1057,' +
                                   '!=4.00.1381,<5')


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


@memoize
def platform_name():
    def run(args):
        return subprocess.run(args, text=True, check=True,
                              stdout=subprocess.PIPE).stdout.strip()

    if 'BFG_FORCE_PLATFORM' in os.environ:
        return os.environ['BFG_FORCE_PLATFORM']

    try:
        uname = run(['uname', '-o']).lower()
        # If this is the Msys `uname`, ignore its output and get the platform
        # another way. (Git for Windows can install `uname` into PATH).
        if uname == 'msys':
            raise OSError()

        # Strip GNU prefix if any since it's not important in this context (or
        # is it? TODO: revisit this decision.)
        uname = re.sub('^gnu/', '', uname)

        if uname == 'linux':
            try:
                distro = run(['lsb_release', '-is']).lower()
                if distro == 'android':
                    return 'android'
            except OSError:
                pass
        elif uname == 'darwin':
            machine = run(['uname', '-m'])
            if re.match(r'(iPhone|iPad|iPod)', machine):
                return 'ios'
            return 'macos'

        # Not sure what this is. Probably a POSIX system though.
        return uname
    except (OSError, subprocess.CalledProcessError):
        system = platform.system().lower()

        if system == 'windows':
            version = Version(platform.version())
            if version not in _non_winnt_versions:
                return 'winnt'
            elif version in SpecifierSet('>=4'):
                return 'win9x'
            return 'msdos'

        # Not sure what this is...
        return system


def platform_tuple(name=None):
    if name is None:
        name = platform_name()
    return _platform_genus.get(name, str(name)), name


class Platform:
    def __init__(self, genus, species, arch):
        self.genus = genus
        self.species = species
        self.arch = arch

    @property
    def name(self):
        return self.species

    @property
    def _triplet_vendor(self):
        return 'pc' if re.match(r'i.86$', self.arch) else 'unknown'

    @property
    def triplet(self):
        return '{}-{}-{}'.format(self.arch, self._triplet_vendor,
                                 self._triplet_sys_abi)

    def __repr__(self):
        return '<{}({})>'.format(type(self).__name__, self.triplet)

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
    eps = metadata.entry_points(group='bfg9000.platforms.{}'.format(kind))
    try:
        entry = eps[genus]
    except KeyError:
        # Fall back to a generic POSIX system if we don't recognize the
        # platform name.
        entry = eps['posix']
    return entry.load()(genus, species, arch)


def _platform_info(kind, name=None, arch=None):
    if name is None:
        name = platform_name()
    if arch is None:
        arch = platform.machine()
    genus, species = platform_tuple(name)
    return _get_platform_info(kind, genus, species, arch)
