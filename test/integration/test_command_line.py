from six import assertRegex

from . import *


class TestCommandLine(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join(examples_dir, '01_executable'), configure=False,
            *args, **kwargs
        )

    def setUp(self):
        os.chdir(this_dir)
        cleandir(self.builddir)

    def checkBuild(self):
        os.chdir(self.builddir)
        self.build(executable('simple'))
        self.assertOutput([executable('simple')], 'hello, world!\n')

    def test_configure(self):
        os.chdir(self.srcdir)
        self.assertPopen(
            ['bfg9000', '--debug', 'configure', self.builddir, '--backend',
             self.backend]
        )
        self.checkBuild()

    def test_configure_into(self):
        self.assertPopen(
            ['bfg9000', '--debug', 'configure-into', self.srcdir,
             self.builddir, '--backend', self.backend]
        )
        self.checkBuild()

    def test_help(self):
        os.chdir(self.srcdir)
        output = self.assertPopen(
            ['bfg9000', 'help', 'configure']
        )
        assertRegex(self, output, r'(?m)^build arguments:$')

    def test_help_explicit_srcdir(self):
        output = self.assertPopen(
            ['bfg9000', 'help', 'configure', self.srcdir]
        )
        assertRegex(self, output, r'(?m)^build arguments:$')

    def test_env(self):
        self.configure(env={'MY_ENV_VAR': 'value'})
        output = self.assertPopen(['bfg9000', 'env'])
        assertRegex(self, output, '(?m)^MY_ENV_VAR=value$')

    def test_env_unique(self):
        self.configure(env={'MY_ENV_VAR': 'value'})
        output = self.assertPopen(['bfg9000', 'env', '-u'])
        self.assertEqual(output, 'MY_ENV_VAR=value\n')

    def test_9k(self):
        os.chdir(self.srcdir)
        self.assertPopen(
            ['9k', '--debug', self.builddir, '--backend', self.backend]
        )
        self.checkBuild()
