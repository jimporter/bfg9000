import os.path

from . import *
pjoin = os.path.join


class TestSharedLibrary(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, pjoin(examples_dir, '02_library'),
            *args, **kwargs
        )

    def test_build(self):
        self.build()
        self.assertOutput([executable('program')], 'hello, library!\n')


class TestStaticLibrary(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'static_library', *args, **kwargs)

    def test_build(self):
        self.build()
        self.assertOutput([executable('program')],
                          'hello, library!\n')


class TestNestedStaticLibrary(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, 'nested_static_library', install=True, *args, **kwargs
        )

    def test_build(self):
        self.build()
        self.assertOutput(
            [executable('program')],
            'hello from inner\nhello from middle\nhello from outer\n'
        )

    @skip_if_backend('msbuild')
    def test_install(self):
        self.build('install')

        self.assertDirectory(self.installdir, [
            pjoin(self.libdir, static_library('inner').path),
            pjoin(self.libdir, static_library('middle').path),
            pjoin(self.libdir, static_library('outer').path),
        ])


@unittest.skipIf(env.platform.name == 'windows',
                 'no versioned libraries on windows')
class TestVersionedLibrary(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, 'versioned_library', install=True, *args, **kwargs
        )

    def test_build(self):
        self.build()
        self.assertOutput([executable('program')], 'hello, library!\n')

    def test_install(self):
        self.build('install')

        self.assertDirectory(self.installdir, [
            pjoin(self.bindir, executable('program').path),
            pjoin(self.libdir, shared_library('library', '1.2.3').path),
            pjoin(self.libdir, shared_library('library', '1').path),
        ])

        os.chdir(self.srcdir)
        cleandir(self.builddir)
        self.assertOutput([pjoin(self.bindir, executable('program').path)],
                          'hello, library!\n')
