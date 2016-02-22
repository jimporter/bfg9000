import os

from .. import shell
from .. import iterutils
from .utils import check_which
from ..file_types import StaticLibrary
from ..path import Path, Root


class ArLinker(object):
    rule_name = command_var = link_var = 'ar'

    def __init__(self, env, lang):
        self.platform = env.platform
        self.lang = lang

        self.command = env.getvar('AR', 'ar')
        check_which(self.command, kind='static linker')

        self.global_args = shell.split(env.getvar('ARFLAGS', 'cru'))

    @property
    def flavor(self):
        return 'ar'

    def can_link(self, format, langs):
        return format == self.platform.object_format

    def __call__(self, cmd, input, output, args=None):
        result = [cmd]
        result.extend(iterutils.iterate(args))
        result.append(output)
        result.extend(iterutils.iterate(input))
        return result

    def output_file(self, name, langs):
        head, tail = os.path.split(name)
        path = os.path.join(head, 'lib' + tail + '.a')
        return StaticLibrary(Path(path, Root.builddir),
                             self.platform.object_format, langs)
