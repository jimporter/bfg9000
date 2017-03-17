import os.path

from . import *
pjoin = os.path.join


class TestInstall(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'install', install=True, *args,
                                 **kwargs)

    def test_default(self):
        self.build()
        self.assertOutput(
            [executable('program')],
            'hello from shared a!\nhello from shared b!\n' +
            'hello from static a!\nhello from static b!\n'
        )

    def _check_installed(self):
        self.build('install')

        extra = []
        if platform_info().has_import_library:
            extra = [pjoin(self.libdir, import_library('shared_a').path)]

        self.assertDirectory(self.installdir, [
            pjoin(self.includedir, 'shared_a.hpp'),
            pjoin(self.includedir, 'static_a.hpp'),
            pjoin(self.bindir, executable('program').path),
            pjoin(self.libdir, shared_library('shared_a').path),
            pjoin(self.libdir, shared_library('shared_b').path),
            pjoin(self.libdir, static_library('static_a').path),
        ] + extra)

    @skip_if_backend('msbuild')
    def test_install(self):
        self.build('install')
        self._check_installed()

        os.chdir(self.srcdir)
        cleandir(self.builddir)
        self.assertOutput(
            [pjoin(self.bindir, executable('program').path)],
            'hello from shared a!\nhello from shared b!\n' +
            'hello from static a!\nhello from static b!\n'
        )

    @skip_if_backend('msbuild')
    def test_install_existing_paths(self):
        makedirs(self.includedir, exist_ok=True)
        makedirs(self.bindir, exist_ok=True)
        makedirs(self.libdir, exist_ok=True)
        self.build('install')
        self._check_installed()

        os.chdir(self.srcdir)
        cleandir(self.builddir)
        self.assertOutput(
            [pjoin(self.bindir, executable('program').path)],
            'hello from shared a!\nhello from shared b!\n' +
            'hello from static a!\nhello from static b!\n'
        )

    @skip_if_backend('msbuild')
    def test_uninstall(self):
        self.build('install')
        self._check_installed()

        self.build('uninstall')
        self.assertDirectory(self.installdir, [])


@unittest.skipIf(platform_name() == 'windows', 'no destdir on windows')
class TestDestDir(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'install', install=True,
                                 configure=False, *args, **kwargs)

    def _check_installed(self, destdir=''):
        self.assertDirectory(destdir + self.installdir, [
            '/tmp' + pjoin(self.includedir, 'shared_a.hpp'),
            '/tmp' + pjoin(self.includedir, 'static_a.hpp'),
            '/tmp' + pjoin(self.bindir, executable('program').path),
            '/tmp' + pjoin(self.libdir, shared_library('shared_a').path),
            '/tmp' + pjoin(self.libdir, shared_library('shared_b').path),
            '/tmp' + pjoin(self.libdir, static_library('static_a').path),
        ])

    @skip_if_backend('msbuild')
    def test_install_destdir(self):
        self.configure(env={'DESTDIR': '/tmp'})
        self.build('install')
        self._check_installed('/tmp')

    @only_if_backend('make')
    def test_install_override_destdir(self):
        self.configure()
        self.build('install', extra_args=['DESTDIR=/tmp'])
        self._check_installed('/tmp')

    @skip_if_backend('msbuild')
    def test_uninstall_destdir(self):
        self.configure(env={'DESTDIR': '/tmp'})
        self.build('install')
        self._check_installed('/tmp')

        self.build('uninstall')
        self.assertDirectory('/tmp' + self.installdir, [])
