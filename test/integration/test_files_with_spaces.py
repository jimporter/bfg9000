import os.path
import re

from . import *


class TestFilesWithSpaces(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'files_with_spaces', *args, **kwargs)

    def test_build(self):
        self.build(executable('quad damage'))
        self.assertOutput([executable('quad damage')], 'QUAD DAMAGE!\n')

    def test_build_sub_dir(self):
        self.build(executable('another file'))
        self.assertOutput([executable('another file')], 'hello from sub dir\n')

    @only_if_backend('make', hide=True)
    def test_dir_sentinels(self):
        self.build(executable('another file'))
        self.assertTrue(os.path.isfile('sub dir/.dir'))

    @skip_if_backend('msbuild')
    def test_script(self):
        assertRegex(self, self.build('script'),
                    re.compile('^hello, world!$', re.MULTILINE))
