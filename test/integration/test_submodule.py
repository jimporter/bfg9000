import tarfile

from . import *


class TestSubmodule(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join(examples_dir, '12_submodules'),
                         configure=False, *args, **kwargs)

    def _check_help(self, args):
        output = self.assertPopen(args)
        self.assertRegex(output, r'(?m)^project-defined arguments:$')
        self.assertRegex(output, (r'(?m)^\s+--enthusiasm N\s+set number of ' +
                                  r'exclamation points in greeting'))
        self.assertRegex(output, (r'(?m)^\s+--name NAME\s+set the name to ' +
                                  r'greet \(default: Alice\)$'))

    def test_build_default(self):
        self.configure()
        self.build(executable('program'))

        env_vars = None
        if env.target_platform.family == 'windows':
            env_vars = {'PATH': os.path.abspath(
                self.target_path(output_file('lib'))
            ) + os.pathsep + os.environ['PATH']}
        self.assertOutput([executable('program')], 'Hello, Alice!\n',
                          extra_env=env_vars)

    def test_build_with_args(self):
        self.configure(extra_args=['--name=Bob', '--enthusiasm=3'])
        self.build(executable('program'))

        env_vars = None
        if env.target_platform.family == 'windows':
            env_vars = {'PATH': os.path.abspath(
                self.target_path(output_file('lib'))
            ) + os.pathsep + os.environ['PATH']}
        self.assertOutput([executable('program')], 'Hello, Bob!!!\n',
                          extra_env=env_vars)

    def test_help(self):
        os.chdir(self.srcdir)
        self._check_help(['bfg9000', 'help', 'configure'])
        self._check_help(['9k', '--help'])

    def test_help_explicit_srcdir(self):
        os.chdir(this_dir)
        self._check_help(['bfg9000', 'help', 'configure', self.srcdir])
        self._check_help(['9k', self.srcdir, '--help'])

    @skip_if_backend('msbuild')
    def test_dist(self):
        dist = output_file('12_submodules.tar.gz')
        self.configure()
        self.build('dist')
        self.assertExists(dist)
        with tarfile.open(self.target_path(dist)) as t:
            self.assertEqual(set(t.getnames()), {
                '12_submodules/build.bfg',
                '12_submodules/options.bfg',
                '12_submodules/program.cpp',
                '12_submodules/lib',
                '12_submodules/lib/build.bfg',
                '12_submodules/lib/options.bfg',
                '12_submodules/lib/library.cpp',
                '12_submodules/lib/library.hpp',
            })
