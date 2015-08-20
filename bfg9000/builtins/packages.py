import os.path
import re
from packaging.version import Version

from . import builtin
from .find import find
from .version import check_version, make_specifier
from .. import path
from ..build_inputs import objectify
from ..file_types import *
from ..iterutils import iterate, listify
from ..platforms import which

class Package(object):
    def __init__(self, includes=None, libraries=None, lib_dirs=None):
        self.includes = includes or []
        self.libraries = libraries or []
        self.lib_dirs = lib_dirs or []

def _find_library(env, name, search_dirs):
    # XXX: Support alternative naming schemes (e.g. libfoo.a vs foo.lib for GCC
    # on Windows)? Also not sure how we'll support other runtimes (e.g. JVM).
    linkers = [env.linker('c', 'shared_library'),
               env.linker('c', 'static_library')]
    for d in search_dirs:
        for i in linkers:
            candidate = i.output_file(os.path.join(d, name))
            if os.path.exists(candidate.path.realize(None)):
                return candidate
    raise ValueError("unable to find package '{}'".format(name))

@builtin.globals('env')
def system_package(env, name):
    return Package([], [_find_library(env, name, env.lib_dirs)])

class BoostPackage(Package):
    def __init__(self, includes=None, libraries=None, lib_dirs=None,
                 version=None):
        Package.__init__(self, includes, libraries, lib_dirs)
        self.version = version

def _boost_version(headers, required_version=None):
    version_hpp = headers.path.append('boost').append('version.hpp')
    with open(version_hpp.realize(None)) as f:
        for line in f:
            m = re.match(r'#\s*define\s+BOOST_LIB_VERSION\s+"([\d_]+)"', line)
            if m:
                version = Version(m.group(1).replace('_', '.'))
                check_version(version, required_version, 'Boost')
                return version
    raise IOError('unable to parse "boost/version.hpp"')

@builtin.globals('env')
def boost_package(env, name=None, version=None):
    version = make_specifier(version)

    root = env.getvar('BOOST_ROOT')
    inc_var = env.getvar('BOOST_INCLUDEDIR', os.path.join(root, 'include')
                         if root else None)
    lib_var = env.getvar('BOOST_LIBRARYDIR', os.path.join(root, 'lib')
                         if root else None)

    if inc_var:
        headers = [HeaderDirectory(inc_var, path.Root.absolute)]
        boost_version = _boost_version(headers[0])
    else:
        # On Windows, check the default install location, which is structured
        # differently from other install locations.
        if env.platform.name == 'windows':
            dirs = find(r'C:\Boost\include', 'boost-*', type='d', flat=True)
            if dirs:
                try:
                    headers = [HeaderDirectory(max(dirs), path.Root.absolute)]
                    boost_version = _boost_version(headers[0])
                    return BoostPackage(headers, lib_dirs=r'C:\Boost\lib',
                                        version=_boost_version(headers[0]))
                except IOError:
                    pass

        if not env.platform.include_dirs:
            raise ValueError('unable to find Boost on system')
        for i in env.platform.include_dirs:
            try:
                headers = [HeaderDirectory(i, path.Root.absolute)]
                boost_version = _boost_version(headers[0])
                break
            except IOError as e:
                pass
        else:
            raise e

    if env.platform.name == 'windows':
        if not env.compiler('c++').auto_link:
            # XXX: Don't require auto-link.
            raise ValueError('Boost on Windows requires auto-link')
        return BoostPackage(headers, lib_dirs=listify(lib_var),
                            version=boost_version)
    else:
        dirs = [lib_var] if lib_var else env.platform.lib_dirs
        libraries = [_find_library(env, 'boost_' + i, dirs)
                     for i in iterate(name)]
        return BoostPackage(headers, libraries=libraries, version=boost_version)

@builtin.globals('env')
def system_executable(env, name):
    return Executable(which(name, env.variables), root=path.Root.absolute)
