import platform
from packaging.specifiers import (
    LegacySpecifier as Specifier, Specifier as PythonSpecifier,
    SpecifierSet as PythonSpecifierSet
)
from packaging.version import (
    Version as PythonVersion, LegacyVersion as Version
)

from .app_version import version as bfg_version

bfg_version = PythonVersion(bfg_version)
python_version = PythonVersion(platform.python_version())


# XXX: Use a LegacySpecifierSet instead once the packaging.specifiers has it.
class SpecifierSet(PythonSpecifierSet):
    def __init__(self, specifiers=''):
        specifiers = [s.strip() for s in specifiers.split(',') if s.strip()]
        parsed = set()
        for specifier in specifiers:
            parsed.add(Specifier(specifier))
        self._specs = frozenset(parsed)
        self._prereleases = None


def check_version(version, specifier, kind):
    msg = "{kind} version {ver} doesn't meet requirement {req}"
    if specifier and version not in specifier:
        raise ValueError(msg.format(kind=kind, ver=version, req=specifier))
