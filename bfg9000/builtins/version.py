from .hooks import builtin, optbuiltin
from .. import versionutils as vu


@builtin
@optbuiltin
def bfg9000_required_version(version=None, python_version=None):
    version = vu.make_specifier(version, prereleases=True)
    python_version = vu.make_specifier(python_version, prereleases=True)

    vu.check_version(vu.bfg_version, version, kind='bfg9000')
    vu.check_version(vu.python_version, python_version, kind='python')


@builtin.getter()
@optbuiltin.getter()
def bfg9000_version():
    return vu.bfg_version
