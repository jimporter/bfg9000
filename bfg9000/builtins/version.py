from .hooks import builtin, optbuiltin
from .. import versioning as v
from ..file_types import objectify


@builtin
@optbuiltin
def bfg9000_required_version(version=None, python_version=None):
    version = objectify(version, v.PythonSpecifierSet, allow_none=True,
                        prereleases=True)
    python_version = objectify(python_version, v.PythonSpecifierSet,
                               allow_none=True, prereleases=True)

    v.check_version(v.bfg_version, version, kind='bfg9000')
    v.check_version(v.python_version, python_version, kind='python')


@builtin.getter()
@optbuiltin.getter()
def bfg9000_version():
    return v.bfg_version
