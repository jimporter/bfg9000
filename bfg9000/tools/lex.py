from itertools import chain

from . import builder
from .. import options as opts, safe_str, shell
from .common import BuildCommand, Builder, choose_builder
from ..file_types import SourceFile
from ..iterutils import iterate
from ..languages import known_langs
from ..path import Path
from ..versioning import detect_version

with known_langs.make('lex') as x:
    x.vars(compiler='LEX', flags='LFLAGS')
    x.exts(source=['.l'])

_posix_cmds = ['lex', 'flex']
_windows_cmds = ['lex', 'flex', 'win_flex']


@builder('lex')
def lex_builder(env):
    cmds = (_windows_cmds if env.host_platform.family == 'windows'
            else _posix_cmds)
    return choose_builder(env, known_langs['lex'], cmds, (LexBuilder,))


class LexBuilder(Builder):
    def __init__(self, env, langinfo, command, version_output):
        Builder.__init__(self, langinfo.name,
                         *self._parse_brand(version_output))

        name = langinfo.var('compiler').lower()
        lflags_name = langinfo.var('flags').lower()
        lflags = shell.split(env.getvar(langinfo.var('flags'), ''))

        self.transpiler = LexCompiler(self, env, name, name, command,
                                      flags=(lflags_name, lflags))

    @staticmethod
    def _parse_brand(version_output):
        if 'flex' in version_output:
            return 'flex', detect_version(version_output)
        return 'unknown', None

    @staticmethod
    def check_command(env, command):
        return env.execute(command + ['--version'], stdout=shell.Mode.pipe,
                           stderr=shell.Mode.devnull)


class LexCompiler(BuildCommand):
    @property
    def deps_flavor(self):
        return None

    @property
    def needs_libs(self):
        return False

    def _call(self, cmd, input, output, flags=None):
        return list(chain(
            cmd, iterate(flags), ['-o', output, input]
        ))

    def _output_lang(self, options):
        filtered = options.filter(opts.lang) if options else None
        if filtered:
            lang = filtered[-1].value
            if lang not in ('c', 'c++'):
                raise ValueError('only c and c++ supported')
            return lang
        return 'c'

    def default_name(self, input, context):
        options = getattr(context, 'user_options', None)
        lang = known_langs[self._output_lang(options)]
        return input.path.stripext('.yy' + lang.default_ext('source')).suffix

    def output_file(self, name, context):
        options = getattr(context, 'user_options', None)
        lang = self._output_lang(options)
        return SourceFile(Path(name), lang)

    def flags(self, options, output=None, mode='normal'):
        flags = []
        for i in options:
            if isinstance(i, opts.define):
                if i.value:
                    flags.append('-D' + i.name + '=' + i.value)
                else:
                    flags.append('-D' + i.name)
            elif isinstance(i, opts.warning):
                for j in i.value:
                    if j == opts.WarningValue.disable:
                        flags.append('-w')
                    else:
                        raise ValueError('unsupported warning level {!r}'
                                         .format(j))
            elif isinstance(i, opts.lang):
                if i.value == 'c++':
                    flags.append('--c++')
            elif isinstance(i, safe_str.stringy_types):
                flags.append(i)
            else:
                raise TypeError('unknown option type {!r}'.format(type(i)))
        return flags
