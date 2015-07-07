import os.path

from . import builtin
from .. import path
from ..file_types import *

class Package(object):
    def __init__(self, includes, libraries):
        self.includes = includes
        self.libraries = libraries

def _find_library(env, name, search_dirs):
    linkers = [env.linker('c', 'shared_library'),
               env.linker('c', 'static_library')]
    for d in search_dirs:
        for i in linkers:
            candidate = i.output_file(os.path.join(d, name))
            if os.path.exists(candidate.path.path):
                return candidate
    raise ValueError('unable to find package {!r}'.format(name))

@builtin
def system_package(build, env, name):
    return Package([], [_find_library(env, name, env.lib_dirs)])

@builtin
def boost_package(build, env, name):
    root = env.getvar('BOOST_ROOT')
    if root:
        headers = [HeaderDirectory(os.path.join(root, 'include'),
                                   source=path.Path.builddir)]
        search_dirs = [os.path.join(root, 'lib')]
    else:
        headers = []
        search_dirs = env.platform.lib_dirs

    return Package(headers, [_find_library(env, 'boost_' + name, search_dirs)])

@builtin
def system_executable(build, env, name):
    for d in env.bin_dirs:
        for ext in env.bin_exts:
            candidate = os.path.join(d, name + ext)
            if os.path.exists(candidate):
                return Executable(candidate, source=path.Path.builddir)
    raise ValueError('unable to find executable {!r}'.format(name))
