import tarfile
import time
from six import assertRegex

from . import *


@skip_if(env.host_platform.name != 'linux',
         'cross-compilation tests only run on linux')
class TestCrossCompile(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join(examples_dir, '01_executable'), configure=False,
            *args, **kwargs
        )

    def test_gcc_linux(self):
        self.configure(extra_args=['--toolchain', os.path.join(
            test_data_dir, 'gcc-linux-toolchain.bfg'
        )])
        self.build('simple')
        self.assertOutput([executable('simple')], 'hello, world!\n')

    def test_gcc_linux_refresh(self):
        toolchain = os.path.join(test_data_dir, 'gcc-linux-toolchain.bfg')
        self.configure(extra_args=['--toolchain', toolchain])
        time.sleep(1)
        self.assertPopen(['touch', toolchain])
        self.build('simple')
        self.assertOutput([executable('simple')], 'hello, world!\n')

    @skip_if('mingw-cross' not in extra_tests, 'skipping mingw cross test')
    def test_mingw_windows(self):
        self.configure(extra_args=['--toolchain', os.path.join(
            test_data_dir, 'mingw-windows-toolchain.bfg'
        )])
        self.build('simple.exe')
        output = self.assertPopen(['file', '-b', 'simple.exe'])
        assertRegex(self, output, r"PE32")
