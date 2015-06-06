import os
import shell

import utils
import file_types
from path import Path

class ArLinker(object):
    def __init__(self, platform):
        self.platform = platform
        self.mode = 'static_library'
        self.command_name = os.getenv('AR', 'ar')
        self.command_var = 'ar'
        self.link_var = 'ar'
        self.name = 'ar'
        self.global_args = shell.split(os.getenv('ARFLAGS', 'cru'))

    def command(self, cmd, input, output, args=None):
        result = [cmd]
        result.extend(utils.iterate(args))
        result.append(output)
        result.extend(utils.iterate(input))
        return result

    def output_file(self, name):
        head, tail = os.path.split(name)
        path = os.path.join(head, 'lib' + tail + '.a')
        return file_types.StaticLibrary(tail, path, Path.builddir)

    @property
    def mode_args(self):
        return []
