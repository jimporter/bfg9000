import os.path
import re
from packaging.version import Version

from .hooks import builtin
from .find import find
from .version import check_version, make_specifier
from ..file_types import SystemExecutable
from ..iterutils import iterate, listify
from ..path import Path, Root
from ..platforms import which


class Package(object):
    def __init__(self, includes=None, libraries=None, lib_dirs=None):
        self.includes = includes or []
        self.libraries = libraries or []
        self.lib_dirs = lib_dirs or []


class BoostPackage(Package):
    def __init__(self, includes=None, libraries=None, lib_dirs=None,
                 version=None):
        Package.__init__(self, includes, libraries, lib_dirs)
        self.version = version


def _boost_version(header, required_version=None):
    version_hpp = header.path.append('boost').append('version.hpp')
    with open(version_hpp.string()) as f:
        for line in f:
            m = re.match(r'#\s*define\s+BOOST_LIB_VERSION\s+"([\d_]+)"', line)
            if m:
                version = Version(m.group(1).replace('_', '.'))
                check_version(version, required_version, 'Boost')
                return version
    raise IOError('unable to parse "boost/version.hpp"')


@builtin.globals('env')
def system_package(env, name, lang='c', kind='any'):
    if kind not in ('any', 'shared', 'static'):
        raise ValueError("kind must be one of 'any', 'shared', or 'static'")
    return Package([], [env.builder(lang).packages.library(name, kind)])


@builtin.globals('env')
def boost_package(env, name=None, version=None):
    version = make_specifier(version)
    pkg = env.builder('c++').packages
    version_hpp = os.path.join('boost', 'version.hpp')

    root = env.getvar('BOOST_ROOT')
    incdir = env.getvar('BOOST_INCLUDEDIR', os.path.join(root, 'include')
                        if root else None)
    libdir = env.getvar('BOOST_LIBRARYDIR', os.path.join(root, 'lib')
                        if root else None)

    if incdir:
        header = pkg.header(version_hpp, [incdir])
        boost_version = _boost_version(header, version)
    else:
        # On Windows, check the default install location, which is structured
        # differently from other install locations.
        if env.platform.name == 'windows':
            dirs = find(r'C:\Boost\include', 'boost-*', type='d', flat=True)
            if dirs:
                try:
                    header = pkg.header(version_hpp, max(dirs))
                    boost_version = _boost_version(header, version)
                    return BoostPackage(
                        includes=[header],
                        lib_dirs=r'C:\Boost\lib',
                        version=boost_version
                    )
                except IOError:
                    pass

        header = pkg.header(version_hpp)
        boost_version = _boost_version(header, version)

    if env.platform.name == 'windows':
        if not env.linker('c++', 'shared_library').auto_link:
            # XXX: Don't require auto-link.
            raise ValueError('Boost on Windows requires auto-link')
        return BoostPackage(
            includes=[header],
            lib_dirs=listify(libdir),
            version=boost_version
        )
    else:
        dirs = [libdir] if libdir else None
        return BoostPackage(
            includes=[header],
            libraries=[pkg.library('boost_' + i, search_dirs=dirs)
                       for i in iterate(name)],
            version=boost_version
        )


@builtin.globals('env')
def system_executable(env, name):
    return SystemExecutable(Path(which(name, env.variables), Root.absolute))
