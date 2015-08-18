import os.path
import re
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from . import builtin
from .find import find
from .. import path
from ..build_inputs import objectify
from ..file_types import *
from ..iterutils import iterate
from ..platforms import which

class Package(object):
    def __init__(self, includes, libraries):
        self.includes = includes
        self.libraries = libraries

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
    def __init__(self, includes, libraries, version):
        Package.__init__(self, includes, libraries)
        self.version = version

def _boost_version(headers):
    version_hpp = headers.path.append('boost').append('version.hpp')
    with open(version_hpp.realize(None)) as f:
        for line in f:
            m = re.match(r'#\s*define\s+BOOST_LIB_VERSION\s+"([\d_]+)"', line)
            if m:
                return Version(m.group(1).replace('_', '.'))
    raise IOError("unable to parse 'boost/version.hpp'")

@builtin.globals('env')
def boost_package(env, name=None, version=None):
    pjoin = os.path.join
    root = env.getvar('BOOST_ROOT')

    inc_var = env.getvar('BOOST_INCLUDEDIR', os.path.join(root, 'include')
                         if root else None)
    lib_var = env.getvar('BOOST_LIBRARYDIR', os.path.join(root, 'lib')
                         if root else None)

    if inc_var:
        headers = [HeaderDirectory(inc_var, root=path.Root.absolute)]
        boost_version = _boost_version(headers[0])
    else:
        include_dirs = env.platform.include_dirs
        if env.platform.name == 'windows':
            dirs = find(r'C:\Boost\include', 'boost-*', type='d', flat=True)
            if dirs:
                include_dirs.insert(0, max(dirs))

        if not include_dirs:
            raise ValueError('unable to find Boost on system')
        for i in include_dirs:
            try:
                headers = [HeaderDirectory(i, root=path.Root.absolute)]
                boost_version = _boost_version(headers[0])
                break
            except IOError as e:
                pass
        else:
            raise e

    if version:
        req_version = objectify(version, SpecifierSet, None)
        if boost_version not in req_version:
            raise ValueError("version {ver} doesn't meet requirement {req}"
                             .format(ver=boost_version, req=req_version))

    if env.platform.name == 'windows':
        if not env.compiler('c++').auto_link:
            # XXX: Don't require auto-link
            raise ValueError('Boost on Windows requires auto-link')
        # XXX: Try to find the appropriate lib directory for auto-link?
        libraries = []
    else:
        dirs = [lib_var] if lib_var else env.platform.lib_dirs
        libraries = [_find_library(env, 'boost_' + i, dirs)
                     for i in iterate(name)]

    return BoostPackage(headers, libraries, boost_version)

@builtin.globals('env')
def system_executable(env, name):
    return Executable(which(name, env.variables), root=path.Root.absolute)
