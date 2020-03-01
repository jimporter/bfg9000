import tarfile

from . import *


class TestUserArgs(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join(examples_dir, '10_custom_args'),
                         configure=False, *args, **kwargs)

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
        self.assertRegex(output, r'(?m)^project-defined arguments:$')
        self.assertRegex(output,
                    r'(?m)^\s+--name NAME\s+set the name to greet$')

    def test_help_explicit_srcdir(self):
        os.chdir(this_dir)
        output = self.assertPopen(
            ['bfg9000', 'help', 'configure', self.srcdir]
        )
        self.assertRegex(output, r'(?m)^project-defined arguments:$')
        self.assertRegex(output,
                    r'(?m)^\s+--name NAME\s+set the name to greet$')

    @skip_if_backend('msbuild')
    def test_dist(self):
        dist = output_file('10_custom_args.tar.gz')
        self.configure()
        self.build('dist')
        self.assertExists(dist)
        with tarfile.open(self.target_path(dist)) as t:
            self.assertEqual(set(t.getnames()), {
                '10_custom_args/build.bfg',
                '10_custom_args/options.bfg',
                '10_custom_args/simple.cpp',
            })
