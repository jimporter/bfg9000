import glob
import os

from .. import *


@skip_if('scala' not in test_features, 'skipping scala tests')
class TestScala(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join('languages', 'scala'), install=True,
                         *args, **kwargs)

    def test_build(self):
        self.build('program.jar')
        for i in glob.glob("*.class*"):
            os.remove(i)
        self.assertOutput(['scala', 'program.jar'], 'hello from scala!\n')

    def test_install(self):
        self.build('install')

        self.assertDirectory(self.installdir, [
            os.path.join(self.libdir, 'program.jar'),
        ])

        os.chdir(self.srcdir)
        cleandir(self.builddir)
        self.assertOutput(
            ['scala', os.path.join(self.libdir, 'program.jar')],
            'hello from scala!\n'
        )
