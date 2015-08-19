import platform
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from . import builtin
from ..version import version as _bfg_version
from ..build_inputs import objectify

_bfg_version = Version(_bfg_version)
_python_version = Version(platform.python_version())

@builtin
def bfg9000_required_version(version=None, python_version=None):
    def ensure_specifier(v):
        if v is None:
            return None
        return objectify(v, SpecifierSet, None, prereleases=True)
    template = "{kind} version {ver} doesn't meet requirement {req}"

    version = ensure_specifier(version)
    python_version = ensure_specifier(python_version)

    if version and _bfg_version not in version:
        raise ValueError(template.format(
            kind='bfg9000', ver=_bfg_version, req=version
        ))

    if python_version and _python_version not in python_version:
        raise ValueError(template.format(
            kind='python', ver=_python_version, req=python_version
        ))
