from . import *
from bfg9000.versioning import SpecifierSet

cxx = env.builder('c++')


class TestWholeArchive(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__('whole_archive', *args, **kwargs)

    @skip_if(cxx.flavor == 'msvc' and cxx.version and
             cxx.version in SpecifierSet('<19'),
             'requires cc builder or msvc 2015 update 2', hide=True)
    def test_build(self):
        self.build()
        self.assertOutput([executable('program')], 'hello, library!\n')
