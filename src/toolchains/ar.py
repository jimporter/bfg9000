import os
import shlex

import native
import utils

class ArLinker(native.NativeLinker):
    def __init__(self, platform):
        native.NativeLinker.__init__(self, platform, 'static_library')
        self.command_name = os.getenv('AR', 'ar')
        self.command_var = 'ar'
        self.link_var = 'ar'
        self.name = 'ar'
        self.global_args = shlex.split(os.getenv('ARFLAGS', 'cru'), posix=False)

    # TODO: Figure out a way to indicate that libs are useless here.
    def command(self, cmd, input, output, libs=None, args=None):
        result = [cmd]
        result.extend(utils.iterate(args))
        result.append(output)
        result.extend(utils.iterate(input))
        return result

    @property
    def mode_args(self):
        return []

    def rpath(self, paths):
        return []
