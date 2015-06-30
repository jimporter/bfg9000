import os.path

from .file_types import *
from .builtins import builtin

class Package(object):
    def __init__(self, includes, libraries):
        self.includes = includes
        self.libraries = libraries

def _find_library(env, search_dirs, name):
    linkers = [env.linker('c', 'shared_library'),
               env.linker('c', 'static_library')]
    for d in search_dirs:
        for i in linkers:
            candidate = i.output_file(os.path.join(d, name))
            if os.path.exists(candidate.path.path):
                return candidate
    return ValueError('unable to find package {}'.format(repr(name)))

@builtin
def system_package(build, env, name):
    return Package([], [_find_library(env, env.platform.lib_dirs, name)])

@builtin
def boost_package(build, env, name):
    root = env.getvar('BOOST_ROOT')
    if root:
        headers = [HeaderDirectory(os.path.join(root, 'include'),
                                   source=Path.builddir)]
        search_dirs = [os.path.join(root, 'lib')]
    else:
        headers = []
        search_dirs = env.platform.lib_dirs

    return Package(headers, [_find_library(env, search_dirs, 'boost_' + name)])
