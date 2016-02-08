import os.path

from .integration import *
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
        self.assertOutput([executable('program')], 'hello, library!\n')


@unittest.skipIf(env.platform.name == 'windows',
                 'no versioned libraries on windows')
class TestVersionedLibrary(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, 'versioned_library', dist=True, *args, **kwargs
        )

    def test_build(self):
        self.build()
        self.assertOutput([executable('program')], 'hello, library!\n')

    def test_install(self):
        self.build('install')

        self.assertExists(pjoin(self.bindir, executable('program').path))
        self.assertExists(pjoin(
            self.libdir, shared_library('library', version='1.2.3').path
        ))
        self.assertExists(pjoin(
            self.libdir, shared_library('library', version='1').path
        ))
        self.assertNotExists(pjoin(
            self.libdir, shared_library('library').path
        ))

        os.chdir(self.srcdir)
        cleandir(self.builddir)
        self.assertOutput([pjoin(self.bindir, executable('program').path)],
                          'hello, library!\n')
