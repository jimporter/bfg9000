import os.path

from .. import *


@skip_if_backend('msbuild')
class TestRc(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join('languages', 'rc'), configure=False,
                         *args, **kwargs)

    @skip_if(env.host_platform.family != 'windows', hide=True)
    def test_native(self):
        self.configure()
        self.build()

    @skip_if('mingw-cross' not in test_features, 'skipping mingw cross test')
    @skip_if(env.host_platform.genus != 'linux', hide=True)
    def test_mingw(self):
        self.configure(extra_args=['--toolchain', os.path.join(
            test_data_dir, 'mingw-windows-toolchain.bfg'
        )])
        self.build()
