import os

from .. import shell
from .. import iterutils
from .common import SimpleCommand
from ..file_types import StaticLibrary
from ..path import Path


class ArLinker(SimpleCommand):
    rule_name = command_var = 'ar'
    flags_var = 'arflags'

    def __init__(self, env, lang):
        SimpleCommand.__init__(self, env, 'AR', 'ar', kind='static linker')
        self.lang = lang
        self.global_args = shell.split(env.getvar('ARFLAGS', 'cru'))

    @property
    def flavor(self):
        return 'ar'

    @property
    def family(self):
        # Don't return a family to prevent people from applying global link
        # options to this linker. (This may change one day.)
        return None

    def can_link(self, format, langs):
        return format == self.env.platform.object_format

    @property
    def has_link_macros(self):
        # We only need to define LIBFOO_EXPORTS/LIBFOO_STATIC macros on
        # platforms that have different import/export rules for libraries. We
        # approximate this by checking if the platform uses import libraries,
        # and only define the macros if it does.
        return self.env.platform.has_import_library

    def _call(self, cmd, input, output, args=None):
        result = [cmd]
        result.extend(iterutils.iterate(args))
        result.append(output)
        result.extend(iterutils.iterate(input))
        return result

    def output_file(self, name, options):
        head, tail = os.path.split(name)
        path = os.path.join(head, 'lib' + tail + '.a')
        return StaticLibrary(Path(path), self.env.platform.object_format,
                             options.langs)
