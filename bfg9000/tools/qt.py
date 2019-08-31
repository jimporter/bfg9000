from itertools import chain

from . import builder
from .. import options as opts, safe_str, shell
from .common import BuildCommand, Builder, choose_builder
from ..file_types import HeaderFile, SourceFile
from ..iterutils import iterate
from ..languages import known_langs
from ..path import Path
from ..versioning import detect_version

with known_langs.make('qtmoc', base='c++') as x:
    x.vars(compiler='MOC', flags='MOCFLAGS')

with known_langs.make('qrc') as x:
    x.vars(compiler='RCC', flags='RCCFLAGS')
    x.exts(resource=['.qrc'])

with known_langs.make('qtui') as x:
    x.vars(compiler='UIC', flags='UICFLAGS')
    x.exts(resource=['.ui'])


@builder('qtmoc')
def moc_builder(env):
    return choose_builder(env, known_langs['qtmoc'], ['moc'], (MocBuilder,))


class MocBuilder(Builder):
    def __init__(self, env, langinfo, command, version_output):
        Builder.__init__(self, langinfo.name,
                         *self._parse_brand(version_output))

        name = langinfo.var('compiler').lower()
        mocflags_name = langinfo.var('flags').lower()
        mocflags = shell.split(env.getvar(langinfo.var('flags'), ''))

        self.transpiler = MocCompiler(self, env, name, name, command,
                                      flags=(mocflags_name, mocflags))

    @staticmethod
    def _parse_brand(version_output):
        if 'moc' in version_output:
            return 'qt', detect_version(version_output)
        return 'unknown', None

    @staticmethod
    def check_command(env, command):
        return env.execute(command + ['--version'], stdout=shell.Mode.pipe,
                           stderr=shell.Mode.devnull)


class MocCompiler(BuildCommand):
    @property
    def deps_flavor(self):
        return None

    @property
    def needs_libs(self):
        return False

    def _call(self, cmd, input, output, flags=None):
        return list(chain(
            cmd, iterate(flags), [input, '-o', output]
        ))

    def default_name(self, input, context):
        if isinstance(input, SourceFile):
            return input.path.stripext('.moc').suffix
        base, leaf = input.path.stripext(
            known_langs['c++'].default_ext('source')
        ).splitleaf()
        return base.append('moc_' + leaf).suffix

    def output_file(self, name, context):
        return SourceFile(Path(name), 'c++')

    def flags(self, options, output=None, mode='normal'):
        flags = []
        for i in options:
            if isinstance(i, opts.include_dir):
                flags.append('-I' + i.directory.path)
            elif isinstance(i, opts.define):
                if i.value:
                    flags.append('-D' + i.name + '=' + i.value)
                else:
                    flags.append('-D' + i.name)
            elif isinstance(i, opts.warning):
                for j in i.value:
                    if j == opts.WarningValue.disable:
                        flags.append('--no-warnings')
                    else:
                        raise ValueError('unsupported warning level {!r}'
                                         .format(j))
            elif isinstance(i, safe_str.stringy_types):
                flags.append(i)
            else:
                raise TypeError('unknown option type {!r}'.format(type(i)))
        return flags


@builder('qrc')
def qrc_builder(env):
    return choose_builder(env, known_langs['qrc'], ['rcc'], (RccBuilder,))


class RccBuilder(Builder):
    def __init__(self, env, langinfo, command, version_output):
        Builder.__init__(self, langinfo.name,
                         *self._parse_brand(version_output))

        name = langinfo.var('compiler').lower()
        rccflags_name = langinfo.var('flags').lower()
        rccflags = shell.split(env.getvar(langinfo.var('flags'), ''))

        self.transpiler = RccCompiler(self, env, name, command, rccflags_name,
                                      rccflags)

    @staticmethod
    def _parse_brand(version_output):
        if 'rcc' in version_output:
            return 'qt', detect_version(version_output)
        return 'unknown', None

    @staticmethod
    def check_command(env, command):
        return env.execute(command + ['--version'], stdout=shell.Mode.pipe,
                           stderr=shell.Mode.devnull)


class RccCompiler(BuildCommand):
    def __init__(self, builder, env, name, command, rccflags_name, rccflags):
        BuildCommand.__init__(self, builder, env, name, name, command,
                              flags=(rccflags_name, rccflags))

    @property
    def deps_flavor(self):
        return 'gcc'

    @property
    def needs_libs(self):
        return False

    def _call(self, cmd, input, output, deps=None, flags=None):
        result = list(chain(cmd, iterate(flags), [input, '-o', output]))
        if deps:
            return self.env.tool('rccdep')(result, deps)
        return result

    def default_name(self, input, context):
        return input.path.stripext(
            known_langs['c++'].default_ext('source')
        ).suffix

    def output_file(self, name, context):
        return SourceFile(Path(name), 'c++')

    def flags(self, options, output=None, mode='normal'):
        flags = []
        for i in options:
            if isinstance(i, safe_str.stringy_types):
                flags.append(i)
            else:
                raise TypeError('unknown option type {!r}'.format(type(i)))
        return flags


@builder('qtui')
def qtui_builder(env):
    return choose_builder(env, known_langs['qtui'], ['uic'], (UicBuilder,))


class UicBuilder(Builder):
    def __init__(self, env, langinfo, command, version_output):
        Builder.__init__(self, langinfo.name,
                         *self._parse_brand(version_output))

        name = langinfo.var('compiler').lower()
        uicflags_name = langinfo.var('flags').lower()
        uicflags = shell.split(env.getvar(langinfo.var('flags'), ''))

        self.transpiler = UicCompiler(self, env, name, command, uicflags_name,
                                      uicflags)

    @staticmethod
    def _parse_brand(version_output):
        if 'uic' in version_output:
            return 'qt', detect_version(version_output)
        return 'unknown', None

    @staticmethod
    def check_command(env, command):
        return env.execute(command + ['--version'], stdout=shell.Mode.pipe,
                           stderr=shell.Mode.devnull)


class UicCompiler(BuildCommand):
    def __init__(self, builder, env, name, command, uicflags_name, uicflags):
        BuildCommand.__init__(self, builder, env, name, name, command,
                              flags=(uicflags_name, uicflags))

    @property
    def deps_flavor(self):
        return None

    @property
    def needs_libs(self):
        return False

    def _call(self, cmd, input, output, flags=None):
        return list(chain(
            cmd, iterate(flags), [input, '-o', output]
        ))

    def default_name(self, input, context):
        base, leaf = input.path.stripext('.h').splitleaf()
        return base.append('ui_' + leaf).suffix

    def output_file(self, name, context):
        return HeaderFile(Path(name), 'c++')

    def flags(self, options, output=None, mode='normal'):
        flags = []
        for i in options:
            if isinstance(i, safe_str.stringy_types):
                flags.append(i)
            else:
                raise TypeError('unknown option type {!r}'.format(type(i)))
        return flags
