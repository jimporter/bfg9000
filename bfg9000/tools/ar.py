import os
from itertools import chain

from .. import options as opts, safe_str, shell
from .common import BuildCommand, check_which, library_macro
from ..file_types import StaticLibrary
from ..iterutils import iterate
from ..objutils import memoize
from ..path import Path
from ..versioning import detect_version


class ArLinker(BuildCommand):
    def __init__(self, builder, env):
        cmd = check_which(env.getvar('AR', 'ar'), env.variables,
                          kind='static linker')
        global_flags = shell.split(env.getvar('ARFLAGS', 'cru'))
        BuildCommand.__init__(self, builder, env, 'ar', 'ar', cmd,
                              flags=('arflags', global_flags))

    @memoize
    def _check_version(self):
        try:
            output = self.env.execute(
                self.command + ['--version'], stdout=shell.Mode.pipe,
                stderr=shell.Mode.devnull
            )
            if 'GNU ar' in output:
                return 'gnu', detect_version(output)
        except (OSError, shell.CalledProcessError):
            pass
        return 'unknown', None

    @property
    def brand(self):
        return self._check_version()[0]

    @property
    def version(self):
        return self._check_version()[1]

    @property
    def flavor(self):
        return 'ar'

    def can_link(self, format, langs):
        return format == self.builder.object_format

    @property
    def has_link_macros(self):
        # We only need to define LIBFOO_EXPORTS/LIBFOO_STATIC macros on
        # platforms that have different import/export rules for libraries. We
        # approximate this by checking if the platform uses import libraries,
        # and only define the macros if it does.
        return self.env.platform.has_import_library

    def compile_options(self, context):
        return (opts.option_list([opts.pic()]) +
                self.forwarded_compile_options(context))

    def forwarded_compile_options(self, context):
        options = opts.option_list()
        if self.has_link_macros:
            options.append(opts.define(library_macro(
                context.name, 'static_library'
            )))
        return options

    def flags(self, options, mode='normal'):
        flags = []
        for i in options:
            if isinstance(i, safe_str.stringy_types):
                flags.append(i)
            else:
                raise TypeError('unknown option type {!r}'.format(type(i)))
        return flags

    def _call(self, cmd, input, output, flags=None):
        return list(chain(
            cmd, iterate(flags), [output], iterate(input)
        ))

    def output_file(self, name, context):
        head, tail = os.path.split(name)
        path = os.path.join(head, 'lib' + tail + '.a')
        return StaticLibrary(Path(path), self.builder.object_format,
                             context.langs)
