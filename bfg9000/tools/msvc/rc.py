from itertools import chain

from ... import options as opts, safe_str, shell
from ..common import Builder, SimpleBuildCommand
from ...arguments.windows import ArgumentParser
from ...file_types import ObjectFile
from ...iterutils import iterate
from ...objutils import memoize
from ...path import Path
from ...versioning import detect_version


class MsvcRcBuilder(Builder):
    def __init__(self, env, langinfo, command, found, version_output):
        super().__init__(langinfo.name, *self._parse_brand(version_output))

        name = langinfo.var('compiler').lower()
        lflags_name = langinfo.var('flags').lower()
        lflags = shell.split(env.getvar(langinfo.var('flags'), ''))

        self.object_format = env.target_platform.object_format
        self.compiler = MsvcRcCompiler(
            self, env, command=(name, command, found),
            flags=(lflags_name, lflags)
        )

    @staticmethod
    def _parse_brand(version_output):
        if 'Microsoft (R)' in version_output:
            return 'msvc', detect_version(version_output)
        return 'unknown', None

    @staticmethod
    def check_command(env, command):
        return env.execute(command + ['-?'], stdout=shell.Mode.pipe,
                           stderr=shell.Mode.devnull)

    @property
    def flavor(self):
        return 'msvc'

    def linker(self, kind):
        return None


class MsvcRcCompiler(SimpleBuildCommand):
    @property
    def deps_flavor(self):
        return None

    @property
    def needs_libs(self):
        return False

    @property
    def needs_package_options(self):
        return False

    def _call(self, cmd, input, output, flags=None):
        return list(chain(
            cmd, self._always_flags, iterate(flags), ['/fo', output, input]
        ))

    @property
    def _always_flags(self):
        return ['/nologo']

    def default_name(self, input, step):
        return input.path.stripext().suffix

    def output_file(self, name, step):
        return ObjectFile(Path(name + '.res'), self.builder.object_format,
                          self.lang)

    def flags(self, options, global_options=None, output=None, mode='normal'):
        flags = []
        for i in options:
            if isinstance(i, opts.include_dir):
                flags.append('/I' + i.directory.path)
            elif isinstance(i, opts.define):
                if i.value:
                    flags.append('/d' + i.name + '=' + i.value)
                else:
                    flags.append('/d' + i.name)
            elif isinstance(i, safe_str.stringy_types):
                flags.append(i)
            else:
                raise TypeError('unknown option type {!r}'.format(type(i)))
        return flags

    @staticmethod
    @memoize
    def __parser():
        parser = ArgumentParser()
        parser.add('/nologo')
        parser.add('/d', type=list, dest='defines')
        parser.add('/I', type=list, dest='includes')

        return parser

    def parse_flags(self, flags):
        result, extra = self.__parser().parse_known(flags)
        result['extra'] = extra
        return result
