import os.path

from . import builtin
from .. import path
from ..file_types import *

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

@builtin
def boost_package(build, env, name):
    root = env.getvar('BOOST_ROOT')
    if root:
        headers = [HeaderDirectory(os.path.join(root, 'include'),
                                   root=path.Root.absolute)]
        search_dirs = [os.path.join(root, 'lib')]
    else:
        headers = []
        search_dirs = env.platform.lib_dirs

    # XXX: Figure out what to do for Windows, which usually has Boost's version
    # number and build settings in the filename.
    return Package(headers, [_find_library(env, 'boost_' + name, search_dirs)])

@builtin
def system_executable(build, env, name):
    for d in env.bin_dirs:
        for ext in env.bin_exts:
            candidate = os.path.join(d, name + ext)
            if os.path.exists(candidate):
                return Executable(candidate, root=path.Root.absolute)
    raise ValueError("unable to find executable '{}'".format(name))
