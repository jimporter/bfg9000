from . import *


@skip_if_backend('msbuild')
class TestLexYacc(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__('lex_yacc', *args, **kwargs)

    def test_build(self):
        self.build()
        self.assertOutput([executable('calc')], input='1+2\nexit\n',
                          output=' = 3\n')
