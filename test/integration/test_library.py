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

        self.assertDirectory(self.distdir, [
            pjoin(self.bindir, executable('program').path),
            pjoin(self.libdir, shared_library('library', '1.2.3').path),
            pjoin(self.libdir, shared_library('library', '1').path),
        ])

        os.chdir(self.srcdir)
        cleandir(self.builddir)
        self.assertOutput([pjoin(self.bindir, executable('program').path)],
                          'hello, library!\n')
