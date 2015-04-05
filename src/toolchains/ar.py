import os

import utils

class ArLinker(object):
    def __init__(self):
        self.command_name = os.getenv('AR', 'ar')
        self.command_var = 'ar'
        self.name = 'ar'

    # TODO: Figure out a way to indicate that libs, pre_args, and post_args
    # are useless here.
    def command(self, cmd, input, output, libs=None, pre_args=None,
                post_args=None):
        result = str(cmd)
        result += ' crs ' + str(output)
        result += ' ' + ' '.join(utils.strlistify(input))
        return result

    @property
    def always_args(self):
        return []
