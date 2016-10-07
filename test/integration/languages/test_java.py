import glob
import os

from .. import *


class TestJava(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join('languages', 'java'), *args, **kwargs
        )

    def test_build(self):
        self.build('program.jar')
        for i in glob.glob("*.class*"):
            os.remove(i)
        self.assertOutput(['java', '-jar', 'program.jar'],
                          'hello from java!\n')


class TestJavaLibrary(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join('languages', 'java_library'), *args, **kwargs
        )

    def test_build(self):
        self.build('program.jar')
        for i in glob.glob("*.class*"):
            os.remove(i)
        self.assertOutput(['java', '-jar', 'program.jar'],
                          'hello from library!\n')
