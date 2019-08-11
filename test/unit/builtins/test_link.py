import mock

from .common import BuiltinTest
from bfg9000.builtins import compile, default, link  # noqa
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
        expected = file_types.Executable(Path('exe', Root.srcdir), None)
        self.assertIs(self.builtin_dict['executable'](expected), expected)

    def test_src_file(self):
        expected = file_types.Executable(
            Path('exe', Root.srcdir),
            self.env.target_platform.object_format, 'c'
        )
        self.assertSame(self.builtin_dict['executable']('exe'), expected)

    def test_make_simple(self):
        linker = self.env.builder('c++').linker('executable')

        result = self.builtin_dict['executable']('exe', ['main.cpp'])
        self.assertSame(result, self.output_file(linker, 'exe', None),
                        exclude={'creator'})

        src = self.builtin_dict['source_file']('main.cpp')
        result = self.builtin_dict['executable']('exe', [src])
        self.assertSame(result, self.output_file(linker, 'exe', None),
                        exclude={'creator'})

        obj = self.builtin_dict['object_file']('main.o', lang='c++')
        result = self.builtin_dict['executable']('exe', [obj])
        self.assertSame(result, self.output_file(linker, 'exe', None),
                        exclude={'creator'})

    def test_make_override_lang(self):
        linker = self.env.builder('c++').linker('executable')

        src = self.builtin_dict['source_file']('main.c', 'c')
        result = self.builtin_dict['executable']('exe', [src], lang='c++')
        self.assertSame(result, self.output_file(linker, 'exe', None),
                        exclude={'creator'})
        self.assertEqual(result.creator.langs, ['c++'])
        self.assertEqual(result.creator.linker.lang, 'c++')

        obj = self.builtin_dict['object_file']('main.o', lang='c')
        result = self.builtin_dict['executable']('exe', [obj], lang='c++')
        self.assertSame(result, self.output_file(linker, 'exe', None),
                        exclude={'creator'})
        self.assertEqual(result.creator.langs, ['c'])
        self.assertEqual(result.creator.linker.lang, 'c++')

    def test_make_no_files(self):
        self.assertRaises(ValueError, self.builtin_dict['executable'],
                          'exe', [])

    def test_make_multiple_formats(self):
        obj1 = file_types.ObjectFile(Path('obj1.o', Root.srcdir), 'elf', 'c')
        obj2 = file_types.ObjectFile(Path('obj2.o', Root.srcdir), 'coff', 'c')
        self.assertRaises(ValueError, self.builtin_dict['executable'],
                          'exe', [obj1, obj2])

    def test_make_no_langs(self):
        obj1 = file_types.ObjectFile(Path('obj1.o', Root.srcdir), 'elf')
        obj2 = file_types.ObjectFile(Path('obj2.o', Root.srcdir), 'elf')
        self.assertRaises(ValueError, self.builtin_dict['executable'],
                          'exe', [obj1, obj2])

    def test_description(self):
        result = self.builtin_dict['executable'](
            'exe', ['main.cpp'], description='my description'
        )
        self.assertEqual(result.creator.description, 'my description')


class TestSharedLibrary(LinkTest):
    def test_identity(self):
        ex = file_types.SharedLibrary(Path('shared', Root.srcdir), None)
        self.assertIs(self.builtin_dict['shared_library'](ex), ex)

    def test_src_file(self):
        expected = file_types.SharedLibrary(
            Path('shared', Root.srcdir),
            self.env.target_platform.object_format, 'c'
        )
        self.assertSame(self.builtin_dict['shared_library']('shared'),
                        expected)

    def test_convert_from_dual(self):
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        self.assertIs(self.builtin_dict['shared_library'](lib), lib.shared)

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
        self.assertSame(result, self.output_file(linker, 'shared', None),
                        exclude={'creator', 'post_install'})

        src = self.builtin_dict['source_file']('main.cpp')
        result = self.builtin_dict['shared_library']('shared', [src])
        self.assertSame(result, self.output_file(linker, 'shared', None),
                        exclude={'creator', 'post_install'})

        obj = self.builtin_dict['object_file']('main.o', lang='c++')
        result = self.builtin_dict['shared_library']('shared', [obj])
        self.assertSame(result, self.output_file(linker, 'shared', None),
                        exclude={'creator', 'post_install'})

    def test_make_soversion(self):
        class Context(object):
            version = '1'
            soversion = '1'

        src = self.builtin_dict['source_file']('main.cpp')
        linker = self.env.builder('c++').linker('shared_library')
        result = self.builtin_dict['shared_library'](
            'shared', [src], version='1', soversion='1'
        )
        self.assertSame(result, self.output_file(linker, 'shared', Context()),
                        exclude={'creator'})

        self.assertRaises(ValueError, self.builtin_dict['shared_library'],
                          'shared', [src], version='1')
        self.assertRaises(ValueError, self.builtin_dict['shared_library'],
                          'shared', [src], soversion='1')

    def test_make_override_lang(self):
        linker = self.env.builder('c++').linker('shared_library')

        src = self.builtin_dict['source_file']('main.c', 'c')
        result = self.builtin_dict['shared_library']('shared', [src],
                                                     lang='c++')
        self.assertSame(result, self.output_file(linker, 'shared', None),
                        exclude={'creator', 'post_install'})
        self.assertEqual(result.creator.langs, ['c++'])
        self.assertEqual(result.creator.linker.lang, 'c++')

        obj = self.builtin_dict['object_file']('main.o', lang='c')
        result = self.builtin_dict['shared_library']('shared', [obj],
                                                     lang='c++')
        self.assertSame(result, self.output_file(linker, 'shared', None),
                        exclude={'creator', 'post_install'})
        self.assertEqual(result.creator.langs, ['c'])
        self.assertEqual(result.creator.linker.lang, 'c++')

    def test_make_no_files(self):
        self.assertRaises(ValueError, self.builtin_dict['shared_library'],
                          'shared', [])

    def test_description(self):
        result = self.builtin_dict['shared_library'](
            'executable', ['main.cpp'], description='my description'
        )
        self.assertEqual(result.creator.description, 'my description')


class TestStaticLibrary(LinkTest):
    class Context(object):
        def __init__(self, langs=['c++']):
            self.langs = langs

    def test_identity(self):
        ex = file_types.StaticLibrary(Path('static', Root.srcdir), None)
        self.assertIs(self.builtin_dict['static_library'](ex), ex)

    def test_src_file(self):
        expected = file_types.StaticLibrary(
            Path('static', Root.srcdir),
            self.env.target_platform.object_format, 'c'
        )
        self.assertSame(self.builtin_dict['static_library']('static'),
                        expected)

    def test_convert_from_dual(self):
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        self.assertIs(self.builtin_dict['static_library'](lib), lib.static)

    def test_convert_from_dual_invalid_args(self):
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        self.assertRaises(TypeError, self.builtin_dict['static_library'],
                          lib, files=['foo.cpp'])

    def test_make_simple(self):
        linker = self.env.builder('c++').linker('static_library')

        result = self.builtin_dict['static_library']('static', ['main.cpp'])
        self.assertSame(result, self.output_file(
            linker, 'static', self.Context()
        ), exclude={'creator', 'forward_opts'})

        src = self.builtin_dict['source_file']('main.cpp')
        result = self.builtin_dict['static_library']('static', [src])
        self.assertSame(result, self.output_file(
            linker, 'static', self.Context()
        ), exclude={'creator', 'forward_opts'})

        obj = self.builtin_dict['object_file']('main.o', lang='c++')
        result = self.builtin_dict['static_library']('static', [obj])
        self.assertSame(result, self.output_file(
            linker, 'static', self.Context()
        ), exclude={'creator', 'forward_opts'})

    def test_make_override_lang(self):
        linker = self.env.builder('c++').linker('static_library')
        static_library = self.builtin_dict['static_library']

        src = self.builtin_dict['source_file']('main.c', 'c')
        result = static_library('static', [src], lang='c++')
        self.assertSame(result, self.output_file(
            linker, 'static', self.Context()
        ), exclude={'creator', 'forward_opts'})
        self.assertEqual(result.creator.langs, ['c++'])
        self.assertEqual(result.creator.linker.lang, 'c++')

        obj = self.builtin_dict['object_file']('main.o', lang='c')
        result = static_library('static', [obj], lang='c++')
        self.assertSame(result, self.output_file(
            linker, 'static', self.Context(['c'])
        ), exclude={'creator', 'forward_opts'})
        self.assertEqual(result.creator.langs, ['c'])
        self.assertEqual(result.creator.linker.lang, 'c++')

    def test_make_no_files(self):
        self.assertRaises(ValueError, self.builtin_dict['static_library'],
                          'static', [])

    def test_description(self):
        result = self.builtin_dict['static_library'](
            'executable', ['main.cpp'], description='my description'
        )
        self.assertEqual(result.creator.description, 'my description')


class TestLibrary(LinkTest):
    def test_identity(self):
        self.env.library_mode = LibraryMode(True, True)
        expected = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        self.assertIs(self.builtin_dict['library'](expected), expected)

    def test_convert_to_shared(self):
        self.env.library_mode = LibraryMode(True, False)
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        self.assertEqual(self.builtin_dict['library'](lib), lib.shared)

    def test_convert_to_static(self):
        self.env.library_mode = LibraryMode(False, True)
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        self.assertEqual(self.builtin_dict['library'](lib), lib.static)

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
        expected = file_types.StaticLibrary(
            Path('library', Root.srcdir),
            self.env.target_platform.object_format, 'c'
        )
        self.assertSame(self.builtin_dict['library']('library'), expected)

    def test_src_file_explicit_static(self):
        expected = file_types.StaticLibrary(
            Path('library', Root.srcdir),
            self.env.target_platform.object_format, 'c'
        )
        self.assertSame(self.builtin_dict['library']('library', kind='static'),
                        expected)

    def test_src_file_explicit_shared(self):
        expected = file_types.SharedLibrary(
            Path('library', Root.srcdir),
            self.env.target_platform.object_format
        )
        self.assertSame(self.builtin_dict['library']('library', kind='shared'),
                        expected)

    def test_src_file_explicit_dual(self):
        self.assertRaises(ValueError, self.builtin_dict['library'], 'library',
                          kind='dual')

    def test_make_simple_shared(self):
        linker = self.env.builder('c++').linker('shared_library')

        result = self.builtin_dict['library']('library', ['main.cpp'],
                                              kind='shared')
        self.assertSame(result, self.output_file(linker, 'library', None),
                        exclude={'creator', 'post_install'})

        src = self.builtin_dict['source_file']('main.cpp')
        result = self.builtin_dict['library']('library', [src], kind='shared')
        self.assertSame(result, self.output_file(linker, 'library', None),
                        exclude={'creator', 'post_install'})

    def test_make_simple_static(self):
        class Context(object):
            langs = ['c++']

        linker = self.env.builder('c++').linker('static_library')

        result = self.builtin_dict['library']('library', ['main.cpp'],
                                              kind='static')
        self.assertSame(result, self.output_file(linker, 'library', Context()),
                        exclude={'creator', 'forward_opts'})

        src = self.builtin_dict['source_file']('main.cpp')
        result = self.builtin_dict['library']('library', [src], kind='static')
        self.assertSame(result, self.output_file(linker, 'library', Context()),
                        exclude={'creator', 'forward_opts'})

    def test_make_simple_dual(self):
        class Context(object):
            langs = ['c++']

        src = self.builtin_dict['source_file']('main.cpp')
        shared_linker = self.env.builder('c++').linker('shared_library')
        static_linker = self.env.builder('c++').linker('static_library')
        with mock.patch('warnings.warn', lambda s: None):
            result = self.builtin_dict['library']('library', [src],
                                                  kind='dual')

        if shared_linker.builder.can_dual_link:
            self.assertSame(result, file_types.DualUseLibrary(
                self.output_file(shared_linker, 'library', None),
                self.output_file(static_linker, 'library', Context())
            ))
        else:
            self.assertSame(result, self.output_file(
                shared_linker, 'library', None
            ), exclude={'creator'})


class TestWholeArchive(BuiltinTest):
    def test_identity(self):
        expected = file_types.WholeArchive(
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        self.assertIs(self.builtin_dict['whole_archive'](expected), expected)

    def test_src_file(self):
        expected = file_types.WholeArchive(
            file_types.StaticLibrary(
                Path('static', Root.srcdir),
                self.env.target_platform.object_format, 'c'
            )
        )
        self.assertSame(link.whole_archive(self.builtin_dict, 'static'),
                        expected)

    def test_convert_from_static(self):
        lib = file_types.StaticLibrary(Path('static', Root.srcdir), None)
        result = self.builtin_dict['whole_archive'](lib)
        self.assertSame(result, file_types.WholeArchive(lib))

    def test_convert_from_static_invalid_args(self):
        lib = file_types.StaticLibrary(Path('static', Root.srcdir), None)
        self.assertRaises(TypeError, self.builtin_dict['whole_archive'], lib,
                          files=['foo.cpp'])
