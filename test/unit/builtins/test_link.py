import mock

from .common import BuiltinTest
from bfg9000.builtins import compile, default, link
from bfg9000 import file_types
from bfg9000.environment import LibraryMode
from bfg9000.iterutils import listify, unlistify
from bfg9000.path import Path, Root


class LinkTest(BuiltinTest):
    def output_file(self, linker, name, context):
        output = linker.output_file(name, context)
        public_output = linker.post_build(self.build, [], output, context)
        return unlistify([i for i in listify(public_output or output)
                          if not i.private])


class TestExecutable(LinkTest):
    def test_identity(self):
        exe = file_types.Executable(Path('executable', Root.srcdir), None)
        result = self.builtin_dict['executable'](exe)
        self.assertEqual(result, exe)

    def test_src_file(self):
        result = self.builtin_dict['executable']('executable')
        self.assertEqual(result, file_types.Executable(
            Path('executable', Root.srcdir), None
        ))

    def test_make_simple(self):
        linker = self.env.builder('c++').linker('executable')

        result = self.builtin_dict['executable']('executable', ['main.cpp'])
        self.assertEqual(result, self.output_file(linker, 'executable', None))

        src = file_types.SourceFile(Path('main.cpp', Root.srcdir))
        result = self.builtin_dict['executable']('executable', [src])
        self.assertEqual(result, self.output_file(linker, 'executable', None))

    def test_make_no_files(self):
        self.assertRaises(ValueError, self.builtin_dict['executable'],
                          'executable', [])


class TestSharedLibrary(LinkTest):
    def test_identity(self):
        lib = file_types.SharedLibrary(Path('shared', Root.srcdir), None)
        result = self.builtin_dict['shared_library'](lib)
        self.assertEqual(result, lib)

    def test_src_file(self):
        result = self.builtin_dict['shared_library']('shared')
        self.assertEqual(result, file_types.SharedLibrary(
            Path('shared', Root.srcdir), None
        ))

    def test_convert_from_dual(self):
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        result = self.builtin_dict['shared_library'](lib)
        self.assertEqual(result, lib.shared)

    def test_convert_from_dual_invalid_args(self):
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        self.assertRaises(TypeError, self.builtin_dict['shared_library'],
                          lib, files=['foo.cpp'])

    def test_make_simple(self):
        linker = self.env.builder('c++').linker('shared_library')

        result = self.builtin_dict['shared_library']('shared', ['main.cpp'])
        self.assertEqual(result, self.output_file(linker, 'shared', None))

        src = file_types.SourceFile(Path('main.cpp', Root.srcdir))
        result = self.builtin_dict['shared_library']('shared', [src])
        self.assertEqual(result, self.output_file(linker, 'shared', None))

    def test_make_soversion(self):
        class Context(object):
            version = '1'
            soversion = '1'

        src = file_types.SourceFile(Path('main.cpp', Root.srcdir))
        linker = self.env.builder('c++').linker('shared_library')
        result = self.builtin_dict['shared_library'](
            'shared', [src], version='1', soversion='1'
        )
        self.assertEqual(result, self.output_file(linker, 'shared', Context()))

        self.assertRaises(ValueError, self.builtin_dict['shared_library'],
                          'shared', [src], version='1')
        self.assertRaises(ValueError, self.builtin_dict['shared_library'],
                          'shared', [src], soversion='1')

    def test_make_no_files(self):
        self.assertRaises(ValueError, self.builtin_dict['shared_library'],
                          'shared', [])


class TestStaticLibrary(LinkTest):
    def test_identity(self):
        lib = file_types.StaticLibrary(Path('static', Root.srcdir), None)
        result = self.builtin_dict['static_library'](lib)
        self.assertEqual(result, lib)

    def test_src_file(self):
        result = self.builtin_dict['static_library']('static')
        self.assertEqual(result, file_types.StaticLibrary(
            Path('static', Root.srcdir), None
        ))

    def test_convert_from_dual(self):
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        result = self.builtin_dict['static_library'](lib)
        self.assertEqual(result, lib.static)

    def test_convert_from_dual_invalid_args(self):
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        self.assertRaises(TypeError, self.builtin_dict['static_library'],
                          lib, files=['foo.cpp'])

    def test_make_simple(self):
        class Context(object):
            langs = ['c++']

        linker = self.env.builder('c++').linker('static_library')

        result = self.builtin_dict['static_library']('static', ['main.cpp'])
        self.assertEqual(result, self.output_file(linker, 'static', Context()))

        src = file_types.SourceFile(Path('main.cpp', Root.srcdir))
        result = self.builtin_dict['static_library']('static', [src])
        self.assertEqual(result, self.output_file(linker, 'static', Context()))

    def test_make_no_files(self):
        self.assertRaises(ValueError, self.builtin_dict['static_library'],
                          'static', [])


class TestLibrary(LinkTest):
    def test_identity(self):
        self.env.library_mode = LibraryMode(True, True)
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        result = self.builtin_dict['library'](lib)
        self.assertEqual(result, lib)

    def test_convert_to_shared(self):
        self.env.library_mode = LibraryMode(True, False)
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        result = self.builtin_dict['library'](lib)
        self.assertEqual(result, lib.shared)

    def test_convert_to_static(self):
        self.env.library_mode = LibraryMode(False, True)
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        result = self.builtin_dict['library'](lib)
        self.assertEqual(result, lib.static)

    def test_convert_invalid_args(self):
        self.env.library_mode = LibraryMode(False, True)
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        self.assertRaises(TypeError, self.builtin_dict['library'], lib,
                          files=['foo.cpp'])

    def test_no_library(self):
        self.env.library_mode = LibraryMode(False, False)
        self.assertRaises(ValueError, self.builtin_dict['library'], 'library')

    def test_src_file(self):
        self.env.library_mode = LibraryMode(True, True)
        result = self.builtin_dict['library']('library')
        self.assertEqual(result, file_types.StaticLibrary(
            Path('library', Root.srcdir), None
        ))

    def test_src_file_explicit_static(self):
        result = self.builtin_dict['library']('library',
                              kind='static')
        self.assertEqual(result, file_types.StaticLibrary(
            Path('library', Root.srcdir), None
        ))

    def test_src_file_explicit_shared(self):
        result = self.builtin_dict['library']('library',
                              kind='shared')
        self.assertEqual(result, file_types.SharedLibrary(
            Path('library', Root.srcdir), None
        ))

    def test_src_file_explicit_dual(self):
        self.assertRaises(ValueError, self.builtin_dict['library'], 'library',
                          kind='dual')

    def test_make_simple_shared(self):
        linker = self.env.builder('c++').linker('shared_library')

        result = self.builtin_dict['library']('library', ['main.cpp'],
                                              kind='shared')
        self.assertEqual(result, self.output_file(linker, 'library', None))

        src = file_types.SourceFile(Path('main.cpp', Root.srcdir))
        result = self.builtin_dict['library']('library', [src], kind='shared')
        self.assertEqual(result, self.output_file(linker, 'library', None))

    def test_make_simple_static(self):
        class Context(object):
            langs = ['c++']

        linker = self.env.builder('c++').linker('static_library')

        result = self.builtin_dict['library']('library', ['main.cpp'],
                                              kind='static')
        self.assertEqual(result, self.output_file(linker, 'library',
                                                  Context()))

        src = file_types.SourceFile(Path('main.cpp', Root.srcdir))
        result = self.builtin_dict['library']('library', [src], kind='static')
        self.assertEqual(result, self.output_file(linker, 'library',
                                                  Context()))

    def test_make_simple_dual(self):
        class Context(object):
            langs = ['c++']

        src = file_types.SourceFile(Path('main.cpp', Root.srcdir))
        shared_linker = self.env.builder('c++').linker('shared_library')
        static_linker = self.env.builder('c++').linker('static_library')
        with mock.patch('warnings.warn', lambda s: None):
            result = self.builtin_dict['library']('library', [src],
                                                  kind='dual')

        if shared_linker.builder.can_dual_link:
            self.assertEqual(result, file_types.DualUseLibrary(
                self.output_file(shared_linker, 'library', None),
                self.output_file(static_linker, 'library', Context())
            ))
        else:
            self.assertEqual(result, self.output_file(shared_linker, 'library',
                                                      None))


class TestWholeArchive(BuiltinTest):
    def test_identity(self):
        lib = file_types.WholeArchive(
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        result = self.builtin_dict['whole_archive'](lib)
        self.assertEqual(result, lib)

    def test_src_file(self):
        result = link.whole_archive(self.builtin_dict, 'static')
        self.assertEqual(result, file_types.WholeArchive(
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        ))

    def test_convert_from_static(self):
        lib = file_types.StaticLibrary(Path('static', Root.srcdir), None)
        result = self.builtin_dict['whole_archive'](lib)
        self.assertEqual(result, file_types.WholeArchive(lib))

    def test_convert_from_static_invalid_args(self):
        lib = file_types.StaticLibrary(Path('static', Root.srcdir), None)
        self.assertRaises(TypeError, self.builtin_dict['whole_archive'], lib,
                          files=['foo.cpp'])
