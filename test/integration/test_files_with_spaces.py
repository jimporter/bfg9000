import os.path

from . import *


class TestFilesWithSpaces(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__('files_with_spaces', *args, **kwargs)

    def test_build(self):
        self.build(executable('quad damage'))
        self.assertOutput([executable('quad damage')], 'QUAD DAMAGE!\n')

    def test_build_sub_dir(self):
        self.build(executable('another file'))
        self.assertOutput([executable('another file')], 'hello from sub dir\n')

    @only_if_backend('make', hide=True)
    def test_dir_sentinels(self):
        self.build(executable('another file'))
        self.assertTrue(os.path.isfile('another file.int/sub dir/.dir'))

    @skip_if_backend('msbuild')
    def test_script(self):
        self.assertRegex(self.build('script'), '(?m)^hello, world!$')
