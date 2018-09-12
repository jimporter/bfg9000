import sys

from . import tool
from .common import SimpleCommand
from ..file_types import SourceFile
from ..languages import known_langs
from ..path import abspath

with known_langs.make('lua') as x:
    x.vars(runner='LUA')
    x.exts(source=['.lua'])

with known_langs.make('perl') as x:
    x.vars(runner='PERL')
    x.exts(source=['.pl'])

with known_langs.make('python') as x:
    x.vars(runner='PYTHON')
    x.exts(source=['.py'])

with known_langs.make('ruby') as x:
    x.vars(runner='RUBY')
    x.exts(source=['.rb'])


class ScriptCommand(SimpleCommand):
    def run_arguments(self, file):
        if isinstance(file, SourceFile):
            return self(file)
        raise TypeError('expected a source file for {} to run'
                        .format(self.rule_name))


def make_script_tool(lang, default_command):
    @tool(lang, lang=lang)
    class ScriptTool(ScriptCommand):
        def __init__(self, env):
            ScriptCommand.__init__(self, env, name=lang,
                                   env_var=known_langs[lang].var('runner'),
                                   default=default_command)

        def _call(self, cmd, file):
            return cmd + [file]

    ScriptTool.__name__ = lang.title()
    return ScriptTool


Lua = make_script_tool('lua', 'lua')
Perl = make_script_tool('perl', 'perl')
Python = make_script_tool('python', abspath(sys.executable))
Ruby = make_script_tool('ruby', 'ruby')
