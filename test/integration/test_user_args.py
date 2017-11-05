from six import assertRegex

from . import *


class TestUserArgs(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join(examples_dir, '10_custom_args'),
            configure=False, *args, **kwargs
        )

    def test_build_default(self):
        self.configure()
        self.build(executable('simple'))
        self.assertOutput([executable('simple')], 'hello from unnamed!\n')

    def test_build_with_args(self):
        self.configure(extra_args=['--name=foo'])
        self.build(executable('simple'))
        self.assertOutput([executable('simple')], 'hello from foo!\n')

    def test_help(self):
        os.chdir(self.srcdir)
        output = self.assertPopen(
            ['bfg9000', 'help', 'configure']
        )
        assertRegex(self, output, r'(?m)^project-defined arguments:$')
        assertRegex(self, output,
                    r'(?m)^\s+--name NAME\s+set the name to greet$')

    def test_help_explicit_srcdir(self):
        output = self.assertPopen(
            ['bfg9000', 'help', 'configure', self.srcdir]
        )
        assertRegex(self, output, r'(?m)^project-defined arguments:$')
        assertRegex(self, output,
                    r'(?m)^\s+--name NAME\s+set the name to greet$')
