import platform
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from .hooks import builtin
from ..version import version as _bfg_version
from ..file_types import objectify

_bfg_version = Version(_bfg_version)
_python_version = Version(platform.python_version())


def make_specifier(s, prereleases=None):
    if s is None:
        return None
    return objectify(s, SpecifierSet, None, prereleases=prereleases)


def check_version(version, specifier, kind):
    msg = "{kind} version {ver} doesn't meet requirement {req}"
    if specifier and version not in specifier:
        raise ValueError(msg.format(kind=kind, ver=version, req=specifier))


@builtin
def bfg9000_required_version(version=None, python_version=None):
    version = make_specifier(version, prereleases=True)
    python_version = make_specifier(python_version, prereleases=True)

    check_version(_bfg_version, version, kind='bfg9000')
    check_version(_python_version, python_version, kind='python')


@builtin.getter()
def bfg9000_version():
    return _bfg_version
