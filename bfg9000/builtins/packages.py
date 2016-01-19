import os.path
import re
from packaging.version import Version

from . import builtin
from .find import find
from .version import check_version, make_specifier
from .. import path
from ..file_types import *
from ..iterutils import iterate, listify
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


class SystemExecutable(Executable):
    pass


def _boost_version(headers, required_version=None):
    version_hpp = headers.path.append('boost').append('version.hpp')
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
    return Package([], [env.builder(lang).lib_finder(name, kind)])


@builtin.globals('env')
def boost_package(env, name=None, version=None):
    version = make_specifier(version)

    root = env.getvar('BOOST_ROOT')
    incdir = env.getvar('BOOST_INCLUDEDIR', os.path.join(root, 'include')
                        if root else None)
    libdir = env.getvar('BOOST_LIBRARYDIR', os.path.join(root, 'lib')
                        if root else None)

    if incdir:
        headers = [HeaderDirectory(incdir, path.Root.absolute, system=True)]
        boost_version = _boost_version(headers[0], version)
    else:
        # On Windows, check the default install location, which is structured
        # differently from other install locations.
        if env.platform.name == 'windows':
            dirs = find(r'C:\Boost\include', 'boost-*', type='d', flat=True)
            if dirs:
                try:
                    headers = [HeaderDirectory(max(dirs), path.Root.absolute,
                                               system=True)]
                    boost_version = _boost_version(headers[0], version)
                    return BoostPackage(headers, lib_dirs=r'C:\Boost\lib',
                                        version=_boost_version(headers[0]))
                except IOError:
                    pass

        if not env.platform.include_dirs:
            raise ValueError('unable to find Boost on system')
        for i in env.platform.include_dirs:
            try:
                headers = [HeaderDirectory(i, path.Root.absolute, system=True)]
                boost_version = _boost_version(headers[0], version)
                break
            except IOError as e:
                pass
        else:
            raise e

    if env.platform.name == 'windows':
        if not env.linker('c++', 'shared_library').auto_link:
            # XXX: Don't require auto-link.
            raise ValueError('Boost on Windows requires auto-link')
        return BoostPackage(
            includes=headers,
            lib_dirs=listify(libdir),
            version=boost_version
        )
    else:
        finder = env.builder('c++').lib_finder
        dirs = [libdir] if libdir else None
        return BoostPackage(
            includes=headers,
            libraries=[ finder('boost_' + i, search_dirs=dirs)
                        for i in iterate(name) ],
            version=boost_version
        )


@builtin.globals('env')
def system_executable(env, name):
    return SystemExecutable(which(name, env.variables), path.Root.absolute)
