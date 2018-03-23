import sys

from . import tool
from .common import SimpleCommand
from ..file_types import SourceFile
from ..languages import language
from ..path import abspath

language('lua', src_exts=['.lua'])
language('perl', src_exts=['.pl'])
language('python', src_exts=['.py'])
language('ruby', src_exts=['.rb'])


class ScriptCommand(SimpleCommand):
    def run_arguments(self, file):
        if isinstance(file, SourceFile):
            return self(file)
        raise TypeError('expected a source file for {} to run'
                        .format(self.rule_name))


@tool('lua', lang='lua')
class Lua(ScriptCommand):
    def __init__(self, env):
        ScriptCommand.__init__(self, env, name='lua', env_var='LUA',
                               default='lua')

    def _call(self, cmd, file):
        return cmd + [file]


@tool('perl', lang='perl')
class Perl(ScriptCommand):
    def __init__(self, env):
        ScriptCommand.__init__(self, env, name='perl', env_var='PERL',
                               default='perl')

    def _call(self, cmd, file):
        return cmd + [file]


@tool('python', lang='python')
class Python(ScriptCommand):
    def __init__(self, env):
        ScriptCommand.__init__(self, env, name='python', env_var='PYTHON',
                               default=abspath(sys.executable))

    def _call(self, cmd, file):
        return cmd + [file]


@tool('ruby', lang='ruby')
class Ruby(ScriptCommand):
    def __init__(self, env):
        ScriptCommand.__init__(self, env, name='ruby', env_var='RUBY',
                               default='ruby')

    def _call(self, cmd, file):
        return cmd + [file]
