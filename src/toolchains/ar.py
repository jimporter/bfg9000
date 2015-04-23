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
        self.global_link_args = shlex.split(os.getenv('ARFLAGS', 'cru'))

    # TODO: Figure out a way to indicate that compile_args are useless here.
    def command(self, cmd, input, output, compile_args=None, link_args=None):
        result = [str(cmd)]
        result.extend(utils.strlistify(link_args))
        result.append(str(output))
        result.extend(utils.strlistify(input))
        return ' '.join(result)

    @property
    def mode_args(self):
        return []
