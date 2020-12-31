import tarfile

from . import *


class TestUserArgs(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join(examples_dir, '11_custom_args'),
                         configure=False, *args, **kwargs)

    def _check_help(self, args):
        output = self.assertPopen(args)
        self.assertRegex(output, r'(?m)^project-defined arguments:$')
        self.assertRegex(output,
                         r'(?m)^\s+--name NAME\s+set the name to greet$')

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
        self._check_help(['bfg9000', 'help', 'configure'])
        self._check_help(['9k', '--help'])

    def test_help_explicit_srcdir(self):
        os.chdir(this_dir)
        self._check_help(['bfg9000', 'help', 'configure', self.srcdir])
        self._check_help(['9k', self.srcdir, '--help'])

    @skip_if_backend('msbuild')
    def test_dist(self):
        dist = output_file('11_custom_args.tar.gz')
        self.configure()
        self.build('dist')
        self.assertExists(dist)
        with tarfile.open(self.target_path(dist)) as t:
            self.assertEqual(set(t.getnames()), {
                '11_custom_args/build.bfg',
                '11_custom_args/options.bfg',
                '11_custom_args/simple.cpp',
            })
