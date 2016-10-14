import glob
import os

from .. import *


class TestJava(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, os.path.join('languages', 'java'),
                                 install=True, *args, **kwargs)

    def test_build(self):
        self.build('program.jar')
        for i in glob.glob("*.class*"):
            os.remove(i)
        self.assertOutput(['java', '-jar', 'program.jar'],
                          'hello from java!\n')

    def test_install(self):
        self.build('install')

        self.assertDirectory(self.installdir, [
            os.path.join(self.bindir, 'program.jar'),
        ])

        os.chdir(self.srcdir)
        cleandir(self.builddir)
        self.assertOutput(
            ['java', '-jar', os.path.join(self.bindir, 'program.jar')],
            'hello from java!\n'
        )


class TestJavaLibrary(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join('languages', 'java_library'), install=True,
            *args, **kwargs
        )

    def test_build(self):
        self.build('program.jar')
        for i in glob.glob("*.class*"):
            os.remove(i)
        self.assertOutput(['java', '-jar', 'program.jar'],
                          'hello from library!\n')

    def test_install(self):
        self.build('install')

        self.assertDirectory(self.installdir, [
            os.path.join(self.bindir, 'lib.jar'),
            os.path.join(self.bindir, 'program.jar'),
        ])

        os.chdir(self.srcdir)
        cleandir(self.builddir)
        self.assertOutput(
            ['java', '-jar', os.path.join(self.bindir, 'program.jar')],
            'hello from library!\n'
        )
