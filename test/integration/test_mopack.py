import os

from . import *


@skip_if_backend('msbuild')
class TestMopack(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join(examples_dir, '07_mopack'),
                         configure=False, install=True, *args, **kwargs)

    def _test_build_install(self, to='world', extra_args=[]):
        self.configure(extra_args=extra_args)
        self.build()

        env_vars = None
        if env.target_platform.family == 'windows':
            env_vars = {'PATH': os.path.abspath(
                self.target_path(output_file('mopack/build/hello'))
            ) + os.pathsep + os.environ['PATH']}
        self.assertOutput([executable('prog')], 'hello, {}!\n'.format(to),
                          extra_env=env_vars)

        self.build('install')
        os.chdir(self.srcdir)
        cleandir(self.builddir)

        extra = []
        if env.target_platform.has_import_library:
            extra = [os.path.join(self.libdir, import_library('hello').path)]

        self.assertDirectory(self.installdir, [
            os.path.join(self.includedir, 'hello.hpp'),
            os.path.join(self.libdir, shared_library('hello').path),
            os.path.join(self.libdir, 'pkgconfig', 'hello.pc'),
            os.path.join(self.bindir, executable('prog').path),
        ] + extra)

        self.assertOutput(
            [os.path.join(self.bindir, executable('prog').path)],
            'hello, {}!\n'.format(to)
        )

    def test_build_install_default(self):
        self._test_build_install()

    def test_build_install_mopack_override(self):
        mopack_override = os.path.join(test_data_dir, 'mopack-override.yml')
        self._test_build_install('bob', ['-p', mopack_override])

    @skip_if('mingw-cross' not in test_features, 'skipping mingw cross test')
    def test_mingw_windows(self):
        self.configure(extra_args=['--toolchain', os.path.join(
            test_data_dir, 'mingw-windows-toolchain.bfg'
        )])
        self.build()

        output = self.assertPopen(['file', '-b', 'prog.exe'])
        self.assertRegex(output, 'PE32')
