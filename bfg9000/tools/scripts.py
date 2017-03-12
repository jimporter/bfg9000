import sys

from . import runner, tool
from .common import SimpleCommand
from ..file_types import SourceFile
from ..languages import language
from ..path import abspath

language('lua', src_exts=['.lua'])
language('perl', src_exts=['.pl'])
language('python', src_exts=['.py'])
language('ruby', src_exts=['.rb'])


@tool('lua')
class Lua(SimpleCommand):
    def __init__(self, env):
        SimpleCommand.__init__(self, env, name='lua', env_var='LUA',
                               default='lua')

    def _call(self, cmd, file):
        return cmd + [file]


@tool('perl')
class Perl(SimpleCommand):
    def __init__(self, env):
        SimpleCommand.__init__(self, env, name='perl', env_var='PERL',
                               default='perl')

    def _call(self, cmd, file):
        return cmd + [file]


@tool('python')
class Python(SimpleCommand):
    def __init__(self, env):
        SimpleCommand.__init__(self, env, name='python', env_var='PYTHON',
                               default=abspath(sys.executable))

    def _call(self, cmd, file):
        return cmd + [file]


@tool('ruby')
class Ruby(SimpleCommand):
    def __init__(self, env):
        SimpleCommand.__init__(self, env, name='ruby', env_var='RUBY',
                               default='ruby')

    def _call(self, cmd, file):
        return cmd + [file]


@runner('lua', 'perl', 'python', 'ruby')
def run_script(env, lang, file):
    if isinstance(file, SourceFile):
        return env.tool(lang)(file)
