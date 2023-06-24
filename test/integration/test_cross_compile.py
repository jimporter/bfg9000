import time

from . import *


@skip_if(env.host_platform.genus != 'linux',
         'cross-compilation tests only run on linux')
class TestCrossCompile(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join(examples_dir, '01_executable'),
                         configure=False, *args, **kwargs)

    def test_gcc_linux(self):
        self.configure(extra_args=['--toolchain', os.path.join(
            test_data_dir, 'gcc-linux-toolchain.bfg'
        )])
        self.build('simple')
        self.assertOutput([executable('simple')], 'hello, world!\n')

    def test_gcc_linux_regenerate(self):
        toolchain = os.path.join(test_data_dir, 'gcc-linux-toolchain.bfg')
        self.configure(extra_args=['--toolchain', toolchain])
        time.sleep(1)
        self.assertPopen(['touch', toolchain])
        self.build('simple')
        self.assertOutput([executable('simple')], 'hello, world!\n')

    @skip_if('mingw-cross' not in test_features, 'skipping mingw cross test')
    def test_mingw_windows(self):
        self.configure(extra_args=['--toolchain', os.path.join(
            test_data_dir, 'mingw-windows-toolchain.bfg'
        )])
        self.build('simple.exe')
        output = self.assertPopen(['file', '-b', 'simple.exe'])
        self.assertRegex(output, 'PE32')


@skip_if(env.host_platform.genus != 'linux',
         'cross-compilation tests only run on linux')
class TestCrossCompileArch(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join('languages', 'c'), configure=False,
                         *args, **kwargs)

    def test_i686(self):
        self.configure(extra_args=['--toolchain', os.path.join(
            test_data_dir, 'i686-toolchain.bfg'
        )])
        self.build(executable('program'))
        self.assertOutput([executable('program')], 'hello from c!\n')

        output = self.assertPopen(['file', '-b', 'program'])
        self.assertRegex(output, 'ELF 32-bit')
