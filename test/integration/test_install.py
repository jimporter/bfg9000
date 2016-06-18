import os.path

from . import *
pjoin = os.path.join


class TestInstall(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'install', dist=True, *args, **kwargs)

    def setUp(self):
        IntegrationTest.setUp(self)
        cleandir(self.distdir)

    def test_default(self):
        self.build()
        self.assertOutput(
            [executable('program')],
            'hello from shared a!\nhello from shared b!\n' +
            'hello from static a!\nhello from static b!\n'
        )

    @skip_if_backend('msbuild')
    def test_install(self):
        self.build('install')

        extra = []
        if platform_info().has_import_library:
            extra = [pjoin(self.libdir, import_library('shared_a').path)]

        self.assertDirectory(self.distdir, [
            pjoin(self.includedir, 'shared_a.hpp'),
            pjoin(self.includedir, 'static_a.hpp'),
            pjoin(self.bindir, executable('program').path),
            pjoin(self.libdir, shared_library('shared_a').path),
            pjoin(self.libdir, shared_library('shared_b').path),
            pjoin(self.libdir, static_library('static_a').path),
        ] + extra)

        os.chdir(self.srcdir)
        cleandir(self.builddir)
        self.assertOutput(
            [os.path.join(self.bindir, executable('program').path)],
            'hello from shared a!\nhello from shared b!\n' +
            'hello from static a!\nhello from static b!\n'
        )

    @skip_if_backend('msbuild')
    def test_install_existing_paths(self):
        makedirs(self.includedir, exist_ok=True)
        makedirs(self.bindir, exist_ok=True)
        makedirs(self.libdir, exist_ok=True)
        self.build('install')

        extra = []
        if platform_info().has_import_library:
            extra = [pjoin(self.libdir, import_library('shared_a').path)]

        self.assertDirectory(self.distdir, [
            pjoin(self.includedir, 'shared_a.hpp'),
            pjoin(self.includedir, 'static_a.hpp'),
            pjoin(self.bindir, executable('program').path),
            pjoin(self.libdir, shared_library('shared_a').path),
            pjoin(self.libdir, shared_library('shared_b').path),
            pjoin(self.libdir, static_library('static_a').path),
        ] + extra)

        os.chdir(self.srcdir)
        cleandir(self.builddir)
        self.assertOutput(
            [os.path.join(self.bindir, executable('program').path)],
            'hello from shared a!\nhello from shared b!\n' +
            'hello from static a!\nhello from static b!\n'
        )
