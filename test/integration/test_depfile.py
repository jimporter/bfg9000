import os.path
import shutil

from . import *


class TestDepfile(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'depfile', stage_src=True,
                                 *args, **kwargs)

    @skip_pred(lambda x: x.backend == 'make' and
               env.host_platform.family == 'windows',
               'xfail on windows + make')
    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')], 'hello\n')

        self.wait()
        shutil.copy(os.path.join(self.srcdir, 'header_replaced.hpp'),
                    os.path.join(self.srcdir, 'header.hpp'))

        self.build(executable('program'))
        self.assertOutput([executable('program')], 'goodbye\n')
