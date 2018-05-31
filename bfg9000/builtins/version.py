from . import builtin
from .. import versioning as v
from ..objutils import objectify


@builtin.function(context='*')
def bfg9000_required_version(version=None, python_version=None):
    version = objectify(version or '', v.PythonSpecifierSet, prereleases=True)
    python_version = objectify(python_version or '', v.PythonSpecifierSet,
                               prereleases=True)

    v.check_version(v.bfg_version, version, kind='bfg9000')
    v.check_version(v.python_version, python_version, kind='python')


@builtin.getter(context='*')
def bfg9000_version():
    return v.bfg_version
