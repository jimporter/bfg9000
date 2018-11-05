import os
import tempfile
import shutil

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
        if env.target_platform.has_import_library:
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


# No DESTDIR on Windows.
@skip_if(env.host_platform.family == 'windows', hide=True)
class TestDestDir(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'install', install=True,
                                 configure=False, *args, **kwargs)

    def setUp(self):
        self.destdir = tempfile.mkdtemp(prefix='destdir-')

    def tearDown(self):
        cleandir(self.destdir, recreate=False)

    def _check_installed(self):
        self.assertDirectory(self.destdir + self.installdir, [
            self.destdir + pjoin(self.includedir, 'shared_a.hpp'),
            self.destdir + pjoin(self.includedir, 'static_a.hpp'),
            self.destdir + pjoin(self.bindir, executable('program').path),
            self.destdir + pjoin(self.libdir, shared_library('shared_a').path),
            self.destdir + pjoin(self.libdir, shared_library('shared_b').path),
            self.destdir + pjoin(self.libdir, static_library('static_a').path),
        ])

    def _check_run(self):
        path = os.path.normpath(self.destdir + self.installdir)
        for i in os.listdir(path):
            shutil.move(pjoin(path, i), self.installdir)
        self.assertOutput(
            [pjoin(self.bindir, executable('program').path)],
            'hello from shared a!\nhello from shared b!\n' +
            'hello from static a!\nhello from static b!\n'
        )

    @skip_if_backend('msbuild')
    def test_install_destdir(self):
        self.configure(env={'DESTDIR': self.destdir})
        self.build('install')
        self._check_installed()
        self._check_run()

    @only_if_backend('make', hide=True)
    def test_install_override_destdir(self):
        self.configure()
        self.build('install', extra_args=['DESTDIR={}'.format(self.destdir)])
        self._check_installed()
        self._check_run()

    @skip_if_backend('msbuild')
    def test_uninstall_destdir(self):
        self.configure(env={'DESTDIR': self.destdir})
        self.build('install')
        self._check_installed()

        self.build('uninstall')
        self.assertDirectory(self.destdir + self.installdir, [])
