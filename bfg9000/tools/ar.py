import os

from .. import shell
from .. import file_types
from .. import iterutils
from ..path import Root

class ArLinker(object):
    def __init__(self, env, command):
        self.platform = env.platform
        self.mode = 'static_library'
        self.command_name = command
        self.command_var = 'ar'
        self.link_var = 'ar'
        self.name = 'ar'
        self.global_args = shell.split(env.getvar('ARFLAGS', 'cru'))

    def command(self, cmd, input, output, args=None):
        result = [cmd]
        result.extend(iterutils.iterate(args))
        result.append(output)
        result.extend(iterutils.iterate(input))
        return result

    def output_file(self, name):
        head, tail = os.path.split(name)
        path = os.path.join(head, 'lib' + tail + '.a')
        return file_types.StaticLibrary(path, Root.builddir)

    @property
    def mode_args(self):
        return []
