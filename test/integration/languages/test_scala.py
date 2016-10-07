import glob
import os

from .. import *


class TestScala(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join('languages', 'scala'), *args, **kwargs
        )

    def test_build(self):
        self.build('program.jar')
        for i in glob.glob("*.class*"):
            os.remove(i)
        self.assertOutput(['scala', 'program.jar'], 'hello from scala!\n')
