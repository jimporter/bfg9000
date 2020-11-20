import os
from functools import partial
from . import *

from bfg9000 import shell

norm = os.path.normpath
pjoin = os.path.join

is_mingw = (env.host_platform.family == 'windows' and
            env.builder('c++').flavor == 'cc')
is_msvc = env.builder('c++').flavor == 'msvc'
pkg_config_cmd = os.getenv('PKG_CONFIG', 'pkg-config')


def pkg_config(args, path='pkgconfig', uninstalled=True):
    env = os.environ.copy()
    env['PKG_CONFIG_PATH'] = os.path.abspath(path)
    if not uninstalled:
        env['PKG_CONFIG_DISABLE_UNINSTALLED'] = '1'
    return shell.execute([pkg_config_cmd] + args, stdout=shell.Mode.pipe,
                         env=env).rstrip().replace('\\\\', '\\')


def readPcFile(filename, field):
    with open(filename) as f:
        for line in f:
            if line.startswith(field + ':'):
                return line[len(field) + 1:].strip()
    raise ValueError('unable to find {!r} field'.format(field))


class PkgConfigTest(IntegrationTest):
    lib_suffix = '.dll' if is_mingw else ''

    def assertPkgConfig(self, args, result, **kwargs):
        self.assertEqual(pkg_config(args, **kwargs), result)

    def _paths(self):
        pkgconfdir = norm(pjoin(self.builddir, 'pkgconfig')).replace('\\', '/')
        return { True: {'include': norm(pjoin(self.srcdir, self.src_include)),
                        'lib': pjoin(pkgconfdir, '..')},
                 False: {'include': norm(self.includedir),
                         'lib': norm(self.libdir)} }

    def _check_requires(self, uninstalled):
        self.assertPkgConfig(['hello', '--print-requires'], '',
                             uninstalled=uninstalled)
        reqs = pkg_config(['hello', '--print-requires-private'],
                          uninstalled=uninstalled)
        if reqs:
            self.assertEqual(reqs, 'ogg')
            return (' ' + pkg_config(['ogg', '--cflags'])).rstrip()
        else:
            return ''


@skip_if_backend('msbuild')
class TestPkgConfig(PkgConfigTest):
    src_include = 'include'

    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join(examples_dir, '12_pkg_config'),
                         configure=False, install=True, *args, **kwargs)

    def test_configure_default(self):
        self.configure()
        self.assertExists(os.path.join('pkgconfig', 'hello.pc'))
        self.assertExists(os.path.join('pkgconfig', 'hello-uninstalled.pc'))

        for u, paths in self._paths().items():
            assertPkgConfig = partial(self.assertPkgConfig, uninstalled=u)
            extra_cflags = self._check_requires(u)

            assertPkgConfig(['hello', '--cflags'],
                            '-I' + paths['include'] + extra_cflags)

            assertPkgConfig(['hello', '--libs-only-L'], '-L' + paths['lib'])
            assertPkgConfig(['hello', '--libs-only-l'],
                            '-lhello{}'.format(self.lib_suffix))
            assertPkgConfig(['hello', '--libs-only-l', '--static'],
                            '-lhello{} -logg'.format(self.lib_suffix))
            assertPkgConfig(['hello', '--libs-only-other'], '')

        self.build('pkg-config-hello')
        self.assertExists(shared_library('hello'))
        if not is_msvc:
            self.assertNotExists(static_library('hello'))

    # Dual-use libraries collide on MSVC.
    @skip_if(is_msvc, hide=True)
    def test_configure_dual(self):
        self.configure(extra_args=['--enable-shared', '--enable-static'])

        hello = os.path.join('pkgconfig', 'hello.pc')
        self.assertExists(hello)
        self.assertEqual(readPcFile(hello, 'Libs'),
                         "-L'${{libdir}}' -lhello{}".format(self.lib_suffix))

        hello_uninst = os.path.join('pkgconfig', 'hello-uninstalled.pc')
        self.assertExists(hello_uninst)
        self.assertEqual(readPcFile(hello_uninst, 'Libs'),
                         "-L'${{builddir}}' -lhello{}".format(self.lib_suffix))

        for u, paths in self._paths().items():
            assertPkgConfig = partial(self.assertPkgConfig, uninstalled=u)
            extra_cflags = self._check_requires(u)

            assertPkgConfig(['hello', '--cflags'],
                            '-I' + paths['include'] + extra_cflags)

            assertPkgConfig(['hello', '--libs-only-L'], '-L' + paths['lib'])
            assertPkgConfig(['hello', '--libs-only-l'],
                            '-lhello{}'.format(self.lib_suffix))
            assertPkgConfig(['hello', '--libs-only-l', '--static'],
                            '-lhello{} -linner -logg'
                            .format(self.lib_suffix))
            assertPkgConfig(['hello', '--libs-only-other'], '')

        self.build('pkg-config-hello')
        self.assertExists(shared_library('hello'))
        if env.target_platform.family == 'windows':
            self.assertExists(import_library('hello'))
        self.assertExists(static_library('hello'))

    def test_configure_static(self):
        self.configure(extra_args=['--disable-shared', '--enable-static'])
        self.assertExists(os.path.join('pkgconfig', 'hello.pc'))
        self.assertExists(os.path.join('pkgconfig', 'hello-uninstalled.pc'))

        for u, paths in self._paths().items():
            assertPkgConfig = partial(self.assertPkgConfig, uninstalled=u)
            extra_cflags = self._check_requires(u)

            assertPkgConfig(['hello', '--cflags'],
                            '-I' + paths['include'] + extra_cflags)

            assertPkgConfig(['hello', '--libs-only-L'], '-L' + paths['lib'])
            assertPkgConfig(['hello', '--libs-only-l'], '-lhello')
            assertPkgConfig(['hello', '--libs-only-l', '--static'],
                            '-lhello -linner -logg')
            assertPkgConfig(['hello', '--libs-only-other'], '')

        self.build('pkg-config-hello')
        self.assertExists(static_library('hello'))
        self.assertNotExists(shared_library('hello'))

    def test_build_sample_prog(self):
        self.configure()
        self.build(executable('sample'))
        self.assertOutput([executable('sample')], 'hello, library!\n')

    def test_install(self):
        self.configure()
        self.build('install')

        os.chdir(self.srcdir)
        cleandir(self.builddir)

        extra = []
        if env.target_platform.has_import_library:
            extra = [os.path.join(self.libdir, import_library('hello').path)]

        self.assertDirectory(self.installdir, [
            os.path.join(self.includedir, 'hello.hpp'),
            os.path.join(self.libdir, shared_library('hello').path),
            os.path.join(self.libdir, shared_library('inner').path),
            os.path.join(self.libdir, 'pkgconfig', 'hello.pc'),
            os.path.join(self.bindir, executable('sample').path),
        ] + extra)

        self.assertOutput(
            [os.path.join(self.bindir, executable('sample').path)],
            'hello, library!\n'
        )

        self.configure(srcdir='pkg_config_use', installdir=None, extra_env={
            'PKG_CONFIG_PATH': os.path.join(self.libdir, 'pkgconfig')
        })
        self.build()

        env_vars = None
        if env.target_platform.family == 'windows':
            env_vars = {'PATH': (os.path.abspath(self.libdir) +
                                 os.pathsep + os.environ['PATH'])}
        self.assertOutput([executable('program')], 'hello, library!\n',
                          extra_env=env_vars)


@skip_if_backend('msbuild')
class TestPkgConfigUsingSystemPkg(PkgConfigTest):
    src_include = 'include'

    def __init__(self, *args, **kwargs):
        super().__init__('pkg_config_system', configure=False, install=True,
                         *args, **kwargs)

    def test_configure(self):
        self.configure(extra_env={'PKG_CONFIG': 'nonexist'})
        self.assertExists(os.path.join('pkgconfig', 'hello.pc'))
        self.assertExists(os.path.join('pkgconfig', 'hello-uninstalled.pc'))

        for u, paths in self._paths().items():
            assertPkgConfig = partial(self.assertPkgConfig, uninstalled=u)
            assertPkgConfig(['hello', '--print-requires'], '')
            assertPkgConfig(['hello', '--print-requires-private'], '')

            assertPkgConfig(['hello', '--cflags'], '-I' + paths['include'])

            assertPkgConfig(['hello', '--libs-only-L'], '-L' + paths['lib'])
            assertPkgConfig(['hello', '--libs-only-l'],
                            '-lhello{}'.format(self.lib_suffix))
            assertPkgConfig(['hello', '--libs-only-l', '--static'],
                            '-lhello{} -logg'.format(self.lib_suffix))
            assertPkgConfig(['hello', '--libs-only-other'], '')


@skip_if_backend('msbuild')
class TestPkgConfigAuto(PkgConfigTest):
    src_include = ''

    def __init__(self, *args, **kwargs):
        super().__init__('pkg_config_auto', configure=False, install=True,
                         *args, **kwargs)

    def test_configure_default(self):
        self.configure()
        self.assertExists(os.path.join('pkgconfig', 'hello.pc'))
        self.assertExists(os.path.join('pkgconfig', 'hello-uninstalled.pc'))

        for u, paths in self._paths().items():
            assertPkgConfig = partial(self.assertPkgConfig, uninstalled=u)
            extra_cflags = self._check_requires(u)

            assertPkgConfig(['hello', '--cflags'],
                            '-I' + paths['include'] + extra_cflags)

            assertPkgConfig(['hello', '--libs-only-L'], '-L' + paths['lib'])
            assertPkgConfig(['hello', '--libs-only-l'],
                            '-lhello{}'.format(self.lib_suffix))
            assertPkgConfig(['hello', '--libs-only-l', '--static'],
                            '-lhello{} -logg'.format(self.lib_suffix))
            assertPkgConfig(['hello', '--libs-only-other'], '')

    # Dual-use libraries collide on MSVC.
    @skip_if(is_msvc, hide=True)
    def test_configure_dual(self):
        self.configure(extra_args=['--enable-shared', '--enable-static'])

        hello = os.path.join('pkgconfig', 'hello.pc')
        self.assertExists(hello)
        self.assertEqual(readPcFile(hello, 'Libs'),
                         "-L'${{libdir}}' -lhello{}".format(self.lib_suffix))

        hello_uninst = os.path.join('pkgconfig', 'hello-uninstalled.pc')
        self.assertExists(hello_uninst)
        self.assertEqual(readPcFile(hello_uninst, 'Libs'),
                         "-L'${{builddir}}' -lhello{}".format(self.lib_suffix))

        for u, paths in self._paths().items():
            assertPkgConfig = partial(self.assertPkgConfig, uninstalled=u)
            extra_cflags = self._check_requires(u)

            assertPkgConfig(['hello', '--cflags'],
                            '-I' + paths['include'] + extra_cflags)

            assertPkgConfig(['hello', '--libs-only-L'], '-L' + paths['lib'])
            assertPkgConfig(['hello', '--libs-only-l'],
                            '-lhello{}'.format(self.lib_suffix))
            assertPkgConfig(['hello', '--libs-only-l', '--static'],
                            '-lhello{} -linner -logg'
                            .format(self.lib_suffix))
            assertPkgConfig(['hello', '--libs-only-other'], '')

    def test_configure_static(self):
        self.configure(extra_args=['--disable-shared', '--enable-static'])
        self.assertExists(os.path.join('pkgconfig', 'hello.pc'))
        self.assertExists(os.path.join('pkgconfig', 'hello-uninstalled.pc'))

        for u, paths in self._paths().items():
            assertPkgConfig = partial(self.assertPkgConfig, uninstalled=u)
            extra_cflags = self._check_requires(u)

            assertPkgConfig(['hello', '--cflags'],
                            '-I' + paths['include'] + extra_cflags)

            assertPkgConfig(['hello', '--libs-only-L'], '-L' + paths['lib'])
            assertPkgConfig(['hello', '--libs-only-l'], '-lhello')
            assertPkgConfig(['hello', '--libs-only-l', '--static'],
                            '-lhello -linner -logg')
            assertPkgConfig(['hello', '--libs-only-other'], '')

    def test_install(self):
        pjoin = os.path.join
        self.configure()
        self.build('install')

        extra = []
        if env.target_platform.has_import_library:
            extra.append(pjoin(self.libdir, import_library('hello').path))

        if env.target_platform.has_versioned_library:
            extra.extend([
                pjoin(self.libdir, shared_library('hello', '1.2.3').path),
                pjoin(self.libdir, shared_library('hello', '1').path),
                pjoin(self.libdir, shared_library('inner', '1.2.3').path),
                pjoin(self.libdir, shared_library('inner', '1').path),
            ])
        else:
            extra.append(pjoin(self.libdir, shared_library('inner').path))

        self.assertDirectory(self.installdir, [
            pjoin(self.includedir, 'hello.hpp'),
            pjoin(self.libdir, shared_library('hello').path),
            pjoin(self.libdir, 'pkgconfig', 'hello.pc'),
        ] + extra)

        self.configure(srcdir='pkg_config_use', installdir=None, extra_env={
            'PKG_CONFIG_PATH': pjoin(self.libdir, 'pkgconfig')
        })
        self.build()

        env_vars = None
        if env.target_platform.family == 'windows':
            env_vars = {'PATH': (os.path.abspath(self.libdir) +
                                 os.pathsep + os.environ['PATH'])}
        self.assertOutput([executable('program')], 'hello, library!\n',
                          extra_env=env_vars)
