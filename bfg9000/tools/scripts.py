import sys

from . import runner, tool
from .utils import SimpleCommand
from ..file_types import SourceFile
from ..languages import language
from ..path import abspath

language('python', src_exts=['.py'])


@tool('lua')
class Lua(SimpleCommand):
    rule_name = command_var = 'lua'

    def __init__(self, env):
        SimpleCommand.__init__(self, env, 'LUA', 'lua')

    def _call(self, cmd, file):
        return [cmd, file]


@tool('perl')
class Perl(SimpleCommand):
    rule_name = command_var = 'perl'

    def __init__(self, env):
        SimpleCommand.__init__(self, env, 'PERL', 'perl')

    def _call(self, cmd, file):
        return [cmd, file]


@tool('python')
class Python(SimpleCommand):
    rule_name = command_var = 'python'

    def __init__(self, env):
        SimpleCommand.__init__(self, env, 'PYTHON', abspath(sys.executable))

    def _call(self, cmd, file):
        return [cmd, file]


@tool('ruby')
class Ruby(SimpleCommand):
    rule_name = command_var = 'ruby'

    def __init__(self, env):
        SimpleCommand.__init__(self, env, 'RUBY', 'ruby')

    def _call(self, cmd, file):
        return [cmd, file]


@runner('lua', 'perl', 'python', 'ruby')
def run_script(env, lang, file):
    if isinstance(file, SourceFile):
        return env.tool(lang)(file)
