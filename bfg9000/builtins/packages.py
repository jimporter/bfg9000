import os.path
import re
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from . import builtin
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

@builtin
def system_package(build, env, name):
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

def _boost_name(env, name):
    if env.platform.name == 'windows':
        # XXX: Support other configurations.
        vs_version = env.getvar('VISUALSTUDIOVERSION').replace('.', '')
        return 'boost_{name}-vc{vs}-mt-{version}'.format(
            name=name, vs=vs_version,
            version=str(curr_version).replace('.', '_')
        )
    else:
        return 'boost_' + name

@builtin
def boost_package(build, env, name=None, version=None):
    root = env.getvar('BOOST_ROOT')
    if root:
        headers = HeaderDirectory(os.path.join(root, 'include'),
                                  root=path.Root.absolute)
        search_dirs = [os.path.join(root, 'lib')]
        curr_version = _boost_version(headers)
    else:
        dirs = env.platform.include_dirs
        search_dirs = env.platform.lib_dirs
        if env.platform.name == 'windows':
            dirs.append(r'C:\Boost')

        for i in dirs:
            try:
                headers = HeaderDirectory(i, root=path.Root.absolute)
                curr_version = _boost_version(headers)
                break
            except IOError as e:
                pass
        else:
            raise e

    if version:
        req_version = objectify(version, SpecifierSet, None)
        if curr_version not in req_version:
            raise ValueError("version {ver} doesn't meet requirement {req}"
                             .format(ver=curr_version, req=req_version))

    if env.platform.name == 'windows':
        # XXX: Support other configurations.
        vs_version = env.getvar('VISUALSTUDIOVERSION').replace('.', '')
        libname = 'boost_{name}-vc{vs}-mt-{version}'.format(
            name=name, vs=vs_version,
            version=str(curr_version).replace('.', '_')
        )
    else:
        libname = 'boost_' + name

    return BoostPackage(
        [headers],
        [_find_library(env, _boost_name(env, i), search_dirs)
         for i in iterate(name)],
        curr_version
    )

@builtin
def system_executable(build, env, name):
    return Executable(which(name, env.variables), root=path.Root.absolute)
