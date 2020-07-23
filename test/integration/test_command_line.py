from . import *


class TestConfigure(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join(examples_dir, '01_executable'),
                         configure=False, *args, **kwargs)

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

    def test_configure_makes_dir(self):
        cleandir(self.builddir, recreate=False)
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

    def test_9k(self):
        os.chdir(self.srcdir)
        self.assertPopen(
            ['9k', '--debug', self.builddir, '--backend', self.backend]
        )
        self.checkBuild()


class TestConfigureErrors(BasicIntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join(examples_dir, '01_executable'),
                         configure=False, *args, **kwargs)

    def test_configure_not_srcdir(self):
        output = self.assertPopen(
            ['bfg9000', 'configure-into', this_dir, self.builddir],
            returncode=2
        )
        self.assertRegex(output,
                         'source directory must contain a build.bfg file')

    def test_configure_not_builddir(self):
        output = self.assertPopen(
            ['bfg9000', 'configure-into', self.srcdir,
             os.path.join(examples_dir, '02_library')],
            returncode=2
        )
        self.assertRegex(output,
                         'build directory must not contain a build.bfg file')

    def test_configure_src_build_same(self):
        output = self.assertPopen(
            ['bfg9000', 'configure-into', self.srcdir, self.srcdir],
            returncode=2
        )
        self.assertRegex(output,
                         'source and build directories must be different')

    def test_configure_nonexistent_dir(self):
        output = self.assertPopen(
            ['bfg9000', 'configure-into', 'nonexist', 'foo'],
            returncode=2
        )
        self.assertRegex(output, "'nonexist' does not exist")

    def test_configure_dir_is_file(self):
        os.chdir(this_dir)
        output = self.assertPopen(
            ['bfg9000', 'configure-into', 'test_command_line.py', 'foo'],
            returncode=2
        )
        self.assertRegex(output, "'test_command_line.py' is not a directory")


class TestHelp(BasicIntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join(examples_dir, '01_executable'),
                         configure=False, *args, **kwargs)

    def test_help_configure(self):
        os.chdir(self.srcdir)
        output = self.assertPopen(['bfg9000', 'help', 'configure'])
        self.assertRegex(output, r'(?m)^build arguments:$')

    def test_help_configure_explicit_srcdir(self):
        os.chdir(this_dir)
        output = self.assertPopen(
            ['bfg9000', 'help', 'configure', self.srcdir]
        )
        self.assertRegex(output, r'(?m)^build arguments:$')

    def test_help_configure_no_srcdir(self):
        os.chdir(this_dir)
        output = self.assertPopen(['bfg9000', 'help', 'configure'])
        self.assertRegex(output, r'(?m)^build arguments:$')


class TestRefresh(BasicIntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join(examples_dir, '01_executable'),
                         configure=False, *args, **kwargs)

    def test_refresh_extra_args(self):
        output = self.assertPopen(['bfg9000', 'refresh', '--foo'],
                                  returncode=2)
        self.assertRegex(output, 'unrecognized arguments: --foo')

    def test_refresh_in_srcdir(self):
        os.chdir(self.srcdir)
        output = self.assertPopen(['bfg9000', 'refresh'], returncode=2)
        self.assertRegex(output,
                         'build directory must not contain a build.bfg file')


class TestEnv(BasicIntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join(examples_dir, '01_executable'),
                         configure=False, *args, **kwargs)

    def test_env(self):
        self.configure(extra_env={'MY_ENV_VAR': 'value'}, backend=backends[0])
        output = self.assertPopen(['bfg9000', 'env'])
        self.assertRegex(output, '(?m)^MY_ENV_VAR=value$')

    def test_env_unique(self):
        self.configure(extra_env={'MY_ENV_VAR': 'value'}, backend=backends[0])
        output = self.assertPopen(['bfg9000', 'env', '-u'])
        self.assertEqual(output, 'MY_ENV_VAR=value\n')

    def test_env_extra_args(self):
        output = self.assertPopen(['bfg9000', 'env', '--foo'], returncode=2)
        self.assertRegex(output, 'unrecognized arguments: --foo')

    def test_env_in_srcdir(self):
        os.chdir(self.srcdir)
        output = self.assertPopen(['bfg9000', 'env'], returncode=2)
        self.assertRegex(output,
                         'build directory must not contain a build.bfg file')


class TestDepfixer(SubprocessTestCase):
    def test_empty_deps(self):
        self.assertOutput(['bfg9000-depfixer'], input='foo:\n', output='')

    def test_multiple_deps(self):
        self.assertOutput(['bfg9000-depfixer'], input='foo: bar baz\n',
                          output='bar:\nbaz:\n')

    def test_invalid(self):
        self.assertPopen(['bfg9000-depfixer'], input='foo\n', returncode=2)


class TestRccDep(SubprocessTestCase):
    def setUp(self):
        self.rcc = os.getenv('RCC', 'rcc')

    def test_invalid(self):
        self.assertPopen(['bfg9000-rccdep', '-o', 'foo', '-d', 'foo.d',
                          self.rcc, 'nonexist'], returncode=2)
