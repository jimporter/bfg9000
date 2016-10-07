import os.path

from .. import *


class TestScala(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join('languages', 'scala'), *args, **kwargs
        )

    def test_build(self):
        self.build('program.jar')
        # XXX: Test running the .jar; this breaks right now because it doesn't
        # include all the necessary .class files.
        self.assertOutput(['scala', 'program'],
                          'hello from scala!\n')
