import os
import shlex

import utils

class ArLinker(object):
    def __init__(self):
        self.command_name = os.getenv('AR', 'ar')
        self.command_var = 'ar'
        self.link_var = 'ar'
        self.name = 'ar'
        self.global_compile_args = None
        self.global_link_args = shlex.split(os.getenv('ARFLAGS', 'cru'),
                                            posix=False)

    # TODO: Figure out a way to indicate that compile_args are useless here.
    def command(self, cmd, input, output, compile_args=None, link_args=None):
        result = [cmd]
        result.extend(utils.listify(link_args))
        result.append(output)
        result.extend(utils.listify(input))
        return result

    @property
    def mode_args(self):
        return []
