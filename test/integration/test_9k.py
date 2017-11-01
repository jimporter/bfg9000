import tarfile

from . import *


class Test9k(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join(examples_dir, '01_executable'), configure=False,
            *args, **kwargs
        )

    def test_build(self):
        os.chdir(self.srcdir)
        cleandir(self.builddir)
        self.assertPopen(
            ['9k', '--debug', self.builddir, '--backend', self.backend]
        )
        os.chdir(self.builddir)

        self.build(executable('simple'))
        self.assertOutput([executable('simple')], 'hello, world!\n')
