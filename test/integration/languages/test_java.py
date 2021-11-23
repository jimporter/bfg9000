import glob
import os

from .. import *


@skip_if('java' not in test_features, 'skipping java tests')
@skip_if_backend('msbuild')
class TestJava(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join('languages', 'java'), install=True,
                         *args, **kwargs)

    def test_build(self):
        self.build('program.jar')
        for i in glob.glob('*.class*'):
            os.remove(i)
        self.assertOutput(['java', '-jar', 'program.jar'],
                          'hello from java!\n')

    def test_install(self):
        self.build('install')

        self.assertDirectory(self.installdir, [
            os.path.join(self.libdir, 'program.jar'),
        ])

        os.chdir(self.srcdir)
        cleandir(self.builddir)
        self.assertOutput(
            ['java', '-jar', os.path.join(self.libdir, 'program.jar')],
            'hello from java!\n'
        )


@skip_if('gcj' not in test_features, 'skipping gcj tests')
class TestGcj(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join('languages', 'java'),
                         extra_env={'JAVAC': os.getenv('GCJ', 'gcj')},
                         *args, **kwargs)

    def test_build(self):
        self.build('program')
        self.assertOutput([executable('program')], 'hello from java!\n')


@skip_if('java' not in test_features, 'skipping java tests')
@skip_if_backend('msbuild')
class TestJavaLibrary(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join('languages', 'java_library'),
                         install=True, *args, **kwargs)

    def test_build(self):
        self.build('program.jar')
        for i in glob.glob('*.class*'):
            os.remove(i)
        self.assertOutput(['java', '-jar', 'program.jar'],
                          'hello from library!\n')

    def test_install(self):
        self.build('install')

        self.assertDirectory(self.installdir, [
            os.path.join(self.libdir, 'lib.jar'),
            os.path.join(self.libdir, 'program.jar'),
        ])

        os.chdir(self.srcdir)
        cleandir(self.builddir)
        self.assertOutput(
            ['java', '-jar', os.path.join(self.libdir, 'program.jar')],
            'hello from library!\n'
        )

    def test_package(self):
        self.build('install')

        self.configure(
            srcdir=os.path.join('languages', 'java_package'), installdir=None,
            extra_env={'CLASSPATH': os.path.join(self.libdir, '*')}
        )
        self.build()
        self.assertOutput(['java', '-jar', 'program.jar'],
                          'hello from library!\n')
