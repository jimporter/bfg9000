from itertools import chain

from . import builder
from .. import options as opts, safe_str, shell
from .common import BuildCommand, Builder, choose_builder
from ..file_types import HeaderFile, SourceFile
from ..iterutils import first, iterate, listify
from ..languages import known_langs
from ..path import Path
from ..versioning import detect_version

with known_langs.make('yacc') as x:
    x.vars(compiler='YACC', flags='YFLAGS')
    x.exts(source=['.y'])

_posix_cmds = ['yacc', 'bison']
_windows_cmds = ['yacc', 'bison', 'win_bison']


@builder('yacc')
def yacc_builder(env):
    cmds = (_windows_cmds if env.host_platform.family == 'windows'
            else _posix_cmds)
    return choose_builder(env, known_langs['yacc'], cmds, (YaccBuilder,))


class YaccBuilder(Builder):
    def __init__(self, env, langinfo, command, version_output):
        Builder.__init__(self, langinfo.name,
                         *self._parse_brand(version_output))

        name = langinfo.var('compiler').lower()
        lflags_name = langinfo.var('flags').lower()
        lflags = shell.split(env.getvar(langinfo.var('flags'), ''))

        self.transpiler = YaccCompiler(self, env, name, name, command,
                                      flags=(lflags_name, lflags))

    @staticmethod
    def _parse_brand(version_output):
        if 'bison' in version_output:
            return 'bison', detect_version(version_output)
        return 'unknown', None

    @staticmethod
    def check_command(env, command):
        return env.execute(command + ['--version'], stdout=shell.Mode.pipe,
                           stderr=shell.Mode.devnull)


class YaccCompiler(BuildCommand):
    @property
    def deps_flavor(self):
        return None

    @property
    def needs_libs(self):
        return False

    @property
    def num_outputs(self):
        return 1

    def _call(self, cmd, input, output, flags=None):
        return list(chain(
            cmd, iterate(flags), [input, '-o', first(output)]
        ))

    def pre_build(self, build, name, context):
        name = listify(name)
        return opts.option_list(['--defines=' + name[1]]
                                if len(name) > 1 else [])

    def _output_lang(self, options):
        filtered = options.filter(opts.lang) if options else None
        if filtered:
            return filtered[-1].value
        return 'c'

    def default_name(self, input, context):
        options = getattr(context, 'user_options', None)
        lang = known_langs[self._output_lang(options)]
        return [
            input.path.stripext('.tab' + lang.default_ext('source')).suffix,
            input.path.stripext('.tab' + lang.default_ext('header')).suffix
        ]

    def output_file(self, name, context):
        name = listify(name)
        options = getattr(context, 'user_options', None)
        lang = self._output_lang(options)
        src = SourceFile(Path(name[0]), lang)

        if len(name) > 2:
            raise ValueError('too many output names')
        elif len(name) == 2:
            return [src, HeaderFile(Path(name[1]), lang)]
        return src

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
                flags.append('--language=' + i.value)
            elif isinstance(i, safe_str.stringy_types):
                flags.append(i)
            else:
                raise TypeError('unknown option type {!r}'.format(type(i)))
        return flags
