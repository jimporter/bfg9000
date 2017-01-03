import platform
from packaging.specifiers import SpecifierSet
# XXX: This should probably be LegacyVersion, but that would make it a lot
# harder to work with SpecifierSets.
from packaging.version import Version

from .version import version as bfg_version
from .file_types import objectify

bfg_version = Version(bfg_version)
python_version = Version(platform.python_version())


def make_specifier(s, prereleases=None):
    if s is None:
        return None
    return objectify(s, SpecifierSet, None, prereleases=prereleases)


def check_version(version, specifier, kind):
    msg = "{kind} version {ver} doesn't meet requirement {req}"
    if specifier and version not in specifier:
        raise ValueError(msg.format(kind=kind, ver=version, req=specifier))
