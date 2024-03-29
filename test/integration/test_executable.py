import tarfile
from os.path import join as pjoin

from . import *


class TestExecutable(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join(examples_dir, '01_executable'),
                         *args, **kwargs)

    def test_build(self):
        self.build(executable('simple'))
        self.assertOutput([executable('simple')], 'hello, world!\n')

    @skip_if_backend('msbuild')
    def test_all(self):
        self.build('all')
        self.assertOutput([executable('simple')], 'hello, world!\n')

    def test_default_and_clean(self):
        def target_path(p, prefix=''):
            return self.target_path(output_file(p), prefix)

        self.build()
        self.assertOutput([executable('simple')], 'hello, world!\n')

        self.clean()
        common = {'.bfg_environ', 'compile_commands.json'}
        files = {
            'ninja': [common | {'.ninja_deps', '.ninja_log', 'build.ninja'}],
            'make': [common | {'Makefile', pjoin('simple.int', '.dir')}],
            'msbuild': [common | {
                '.bfg_uuid', 'simple.sln', pjoin('simple', 'simple.vcxproj'),
                target_path('simple.Build.CppClean.log', prefix='simple'),
            }, {
                target_path('simple.exe.recipe', prefix='simple'),
                target_path('simple.vcxproj.FileListAbsolute.txt',
                            prefix='simple'),
            }],
        }
        self.assertDirectory('.', *files[self.backend])

    @skip_if_backend('msbuild')
    def test_dist(self):
        dist = output_file('simple-1.0.tar.gz')
        self.build('dist')
        self.assertExists(dist)
        with tarfile.open(self.target_path(dist)) as t:
            self.assertEqual(set(t.getnames()), {
                'simple-1.0/build.bfg',
                'simple-1.0/simple.cpp',
            })
