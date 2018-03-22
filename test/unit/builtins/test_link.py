import unittest

from bfg9000.builtins import builtin, link
from bfg9000 import file_types
from bfg9000.build_inputs import BuildInputs
from bfg9000.environment import Environment, LibraryMode
from bfg9000.path import Path, Root


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.env = Environment(None, None, None, None, None, {},
                               (False, False), None)
        self.build = BuildInputs(self.env, Path('build.bfg', Root.srcdir))
        self.builtin_dict = builtin.bind(build_inputs=self.build, env=self.env)


class TestExecutable(BaseTest):
    def test_identity(self):
        exe = file_types.Executable(Path('executable', Root.srcdir), None)
        result = link.executable(None, self.build, self.env, exe)
        self.assertEqual(result, exe)

    def test_src_file(self):
        result = link.executable(None, self.build, self.env, 'executable')
        self.assertEqual(result, file_types.Executable(
            Path('executable', Root.srcdir), None
        ))


class TestSharedLibrary(BaseTest):
    def test_identity(self):
        lib = file_types.SharedLibrary(Path('shared', Root.srcdir), None)
        result = link.shared_library(None, self.build, self.env, lib)
        self.assertEqual(result, lib)

    def test_src_file(self):
        result = link.shared_library(None, self.build, self.env, 'shared')
        self.assertEqual(result, file_types.SharedLibrary(
            Path('shared', Root.srcdir), None
        ))

    def test_convert_from_dual(self):
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        result = link.shared_library(None, self.build, self.env, lib)
        self.assertEqual(result, lib.shared)

    def test_convert_from_dual_invalid_args(self):
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        self.assertRaises(TypeError, link.shared_library, None, self.build,
                          self.env, lib, files=['foo.cpp'])


class TestStaticLibrary(BaseTest):
    def test_identity(self):
        lib = file_types.StaticLibrary(Path('static', Root.srcdir), None)
        result = link.static_library(None, self.build, self.env, lib)
        self.assertEqual(result, lib)

    def test_src_file(self):
        result = link.static_library(None, self.build, self.env, 'static')
        self.assertEqual(result, file_types.StaticLibrary(
            Path('static', Root.srcdir), None
        ))

    def test_convert_from_dual(self):
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        result = link.static_library(None, self.build, self.env, lib)
        self.assertEqual(result, lib.static)

    def test_convert_from_dual_invalid_args(self):
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        self.assertRaises(TypeError, link.static_library, None, self.build,
                          self.env, lib, files=['foo.cpp'])


class TestLibrary(BaseTest):
    def test_identity(self):
        self.env.library_mode = LibraryMode(True, True)
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        result = link.library(None, self.build, self.env, lib)
        self.assertEqual(result, lib)

    def test_convert_to_shared(self):
        self.env.library_mode = LibraryMode(True, False)
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        result = link.library(None, self.build, self.env, lib)
        self.assertEqual(result, lib.shared)

    def test_convert_to_static(self):
        self.env.library_mode = LibraryMode(False, True)
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        result = link.library(None, self.build, self.env, lib)
        self.assertEqual(result, lib.static)

    def test_convert_invalid_args(self):
        self.env.library_mode = LibraryMode(False, True)
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        self.assertRaises(TypeError, link.library, None, self.build, self.env,
                          lib, files=['foo.cpp'])

    def test_no_library(self):
        self.env.library_mode = LibraryMode(False, False)
        self.assertRaises(ValueError, link.library, None, self.build, self.env,
                          'library')

    def test_src_file(self):
        self.env.library_mode = LibraryMode(True, True)
        result = link.library(None, self.build, self.env, 'library')
        self.assertEqual(result, file_types.StaticLibrary(
            Path('library', Root.srcdir), None
        ))

    def test_src_file_explicit_static(self):
        result = link.library(None, self.build, self.env, 'library',
                              kind='static')
        self.assertEqual(result, file_types.StaticLibrary(
            Path('library', Root.srcdir), None
        ))

    def test_src_file_explicit_shared(self):
        result = link.library(None, self.build, self.env, 'library',
                              kind='shared')
        self.assertEqual(result, file_types.SharedLibrary(
            Path('library', Root.srcdir), None
        ))

    def test_src_file_explicit_dual(self):
        self.assertRaises(ValueError, link.library, None, self.build, self.env,
                          'library', kind='dual')


class TestWholeArchive(BaseTest):
    def test_identity(self):
        lib = file_types.WholeArchive(
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        result = link.whole_archive(None, lib)
        self.assertEqual(result, lib)

    def test_src_file(self):
        result = link.whole_archive(self.builtin_dict, 'static')
        self.assertEqual(result, file_types.WholeArchive(
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        ))

    def test_convert_from_static(self):
        lib = file_types.StaticLibrary(Path('static', Root.srcdir), None)
        result = link.whole_archive(None, lib)
        self.assertEqual(result, file_types.WholeArchive(lib))

    def test_convert_from_static_invalid_args(self):
        lib = file_types.StaticLibrary(Path('static', Root.srcdir), None)
        self.assertRaises(TypeError, link.whole_archive, None, lib,
                          files=['foo.cpp'])
