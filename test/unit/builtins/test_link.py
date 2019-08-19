import mock
from six import iteritems

from .common import AttrDict, BuiltinTest
from bfg9000.builtins import compile, default, link  # noqa
from bfg9000 import file_types
from bfg9000.environment import LibraryMode
from bfg9000.iterutils import listify, unlistify
from bfg9000.options import option_list
from bfg9000.path import Path, Root


class LinkTest(BuiltinTest):
    def output_file(self, name, context={}, lang='c++', mode=None, extra={}):
        linker = self.env.builder(lang).linker(mode or self.mode)
        context_args = {'langs': [lang]}
        context_args.update(context)
        context = AttrDict(**context_args)

        output = linker.output_file(name, context)
        public_output = linker.post_build(self.build, [], output, context)

        result = [i for i in listify(public_output or output) if not i.private]
        for i in result:
            for k, v in iteritems(extra):
                setattr(i, k, v)
        return unlistify(result)


class TestExecutable(LinkTest):
    mode = 'executable'

    def test_identity(self):
        expected = file_types.Executable(Path('exe', Root.srcdir), None)
        self.assertIs(self.builtin_dict['executable'](expected), expected)

    def test_src_file(self):
        expected = file_types.Executable(
            Path('exe', Root.srcdir),
            self.env.target_platform.object_format, 'c'
        )
        self.assertSameFile(self.builtin_dict['executable']('exe'), expected)

    def test_make_simple(self):
        result = self.builtin_dict['executable']('exe', ['main.cpp'])
        self.assertSameFile(result, self.output_file('exe'))

        src = self.builtin_dict['source_file']('main.cpp')
        result = self.builtin_dict['executable']('exe', [src])
        self.assertSameFile(result, self.output_file('exe'))

        obj = self.builtin_dict['object_file']('main.o', lang='c++')
        result = self.builtin_dict['executable']('exe', [obj])
        self.assertSameFile(result, self.output_file('exe'))

    def test_make_override_lang(self):
        expected = self.output_file('exe')

        src = self.builtin_dict['source_file']('main.c', 'c')
        result = self.builtin_dict['executable']('exe', [src], lang='c++')
        self.assertSameFile(result, expected)
        self.assertEqual(result.creator.langs, ['c++'])
        self.assertEqual(result.creator.linker.lang, 'c++')

        obj = self.builtin_dict['object_file']('main.o', lang='c')
        result = self.builtin_dict['executable']('exe', [obj], lang='c++')
        self.assertSameFile(result, expected)
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
    mode = 'shared_library'

    def test_identity(self):
        ex = file_types.SharedLibrary(Path('shared', Root.srcdir), None)
        self.assertIs(self.builtin_dict['shared_library'](ex), ex)

    def test_src_file(self):
        expected = file_types.SharedLibrary(
            Path('shared', Root.srcdir),
            self.env.target_platform.object_format, 'c'
        )
        self.assertSameFile(self.builtin_dict['shared_library']('shared'),
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
        expected = self.output_file('shared')

        result = self.builtin_dict['shared_library']('shared', ['main.cpp'])
        self.assertSameFile(result, expected, exclude={'post_install'})

        src = self.builtin_dict['source_file']('main.cpp')
        result = self.builtin_dict['shared_library']('shared', [src])
        self.assertSameFile(result, expected, exclude={'post_install'})

        obj = self.builtin_dict['object_file']('main.o', lang='c++')
        result = self.builtin_dict['shared_library']('shared', [obj])
        self.assertSameFile(result, expected, exclude={'post_install'})

    def test_make_soversion(self):
        src = self.builtin_dict['source_file']('main.cpp')
        result = self.builtin_dict['shared_library'](
            'shared', [src], version='1', soversion='1'
        )
        self.assertSameFile(result, self.output_file(
            'shared', context={'version': '1', 'soversion': '1'}
        ), exclude={'post_install'})

        self.assertRaises(ValueError, self.builtin_dict['shared_library'],
                          'shared', [src], version='1')
        self.assertRaises(ValueError, self.builtin_dict['shared_library'],
                          'shared', [src], soversion='1')

    def test_make_override_lang(self):
        shared_library = self.builtin_dict['shared_library']
        expected = self.output_file('shared')

        src = self.builtin_dict['source_file']('main.c', 'c')
        result = shared_library('shared', [src], lang='c++')
        self.assertSameFile(result, expected, exclude={'post_install'})
        self.assertEqual(result.creator.langs, ['c++'])
        self.assertEqual(result.creator.linker.lang, 'c++')

        obj = self.builtin_dict['object_file']('main.o', lang='c')
        result = shared_library('shared', [obj], lang='c++')
        self.assertSameFile(result, expected, exclude={'post_install'})
        self.assertEqual(result.creator.langs, ['c'])
        self.assertEqual(result.creator.linker.lang, 'c++')

    def test_make_runtime_deps(self):
        shared_library = self.builtin_dict['shared_library']
        libfoo = shared_library('foo', ['foo.cpp'])

        expected = self.output_file('shared')
        expected.runtime_file.runtime_deps = [libfoo.runtime_file]
        result = shared_library('shared', ['main.cpp'], libs=[libfoo])
        self.assertSameFile(result, expected, exclude={'post_install'})

    def test_make_no_files(self):
        self.assertRaises(ValueError, self.builtin_dict['shared_library'],
                          'shared', [])

    def test_description(self):
        result = self.builtin_dict['shared_library'](
            'executable', ['main.cpp'], description='my description'
        )
        self.assertEqual(result.creator.description, 'my description')


class TestStaticLibrary(LinkTest):
    mode = 'static_library'

    def extra(self, lang='c++', libs=[], **kwargs):
        linker = self.env.builder(lang).linker(self.mode)
        extra = {'forward_opts': {
            'compile_options': linker.forwarded_compile_options(
                AttrDict(name='libstatic')
            ),
            'link_options': option_list(),
            'libs': libs,
            'packages': [],
        }}
        extra.update(kwargs)
        return extra

    def test_identity(self):
        ex = file_types.StaticLibrary(Path('static', Root.srcdir), None)
        self.assertIs(self.builtin_dict['static_library'](ex), ex)

    def test_src_file(self):
        expected = file_types.StaticLibrary(
            Path('static', Root.srcdir),
            self.env.target_platform.object_format, 'c'
        )
        self.assertSameFile(self.builtin_dict['static_library']('static'),
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
        expected = self.output_file('static', extra=self.extra())

        result = self.builtin_dict['static_library']('static', ['main.cpp'])
        self.assertSameFile(result, expected)

        src = self.builtin_dict['source_file']('main.cpp')
        result = self.builtin_dict['static_library']('static', [src])
        self.assertSameFile(result, expected)

        obj = self.builtin_dict['object_file']('main.o', lang='c++')
        result = self.builtin_dict['static_library']('static', [obj])
        self.assertSameFile(result, expected)

    def test_make_override_lang(self):
        static_library = self.builtin_dict['static_library']

        src = self.builtin_dict['source_file']('main.c', 'c')
        result = static_library('static', [src], lang='c++')
        self.assertSameFile(result, self.output_file(
            'static', extra=self.extra()
        ))
        self.assertEqual(result.creator.langs, ['c++'])
        self.assertEqual(result.creator.linker.lang, 'c++')

        obj = self.builtin_dict['object_file']('main.o', lang='c')
        result = static_library('static', [obj], lang='c++')
        self.assertSameFile(result, self.output_file(
            'static', lang='c', extra=self.extra('c')
        ))
        self.assertEqual(result.creator.langs, ['c'])
        self.assertEqual(result.creator.linker.lang, 'c++')

    def test_make_linktime_deps(self):
        static_library = self.builtin_dict['static_library']
        libfoo = static_library('libfoo.a')

        result = static_library('static', ['main.c'], libs=[libfoo])
        self.assertSameFile(result, self.output_file(
            'static', lang='c',
            extra=self.extra('c', [libfoo], linktime_deps=[libfoo])
        ))

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
        self.assertSameFile(self.builtin_dict['library']('library'), expected)

    def test_src_file_explicit_static(self):
        expected = file_types.StaticLibrary(
            Path('library', Root.srcdir),
            self.env.target_platform.object_format, 'c'
        )
        self.assertSameFile(self.builtin_dict['library'](
            'library', kind='static'
        ), expected)

    def test_src_file_explicit_shared(self):
        expected = file_types.SharedLibrary(
            Path('library', Root.srcdir),
            self.env.target_platform.object_format
        )
        self.assertSameFile(self.builtin_dict['library'](
            'library', kind='shared'
        ), expected)

    def test_src_file_explicit_dual(self):
        self.assertRaises(ValueError, self.builtin_dict['library'], 'library',
                          kind='dual')

    def test_make_simple_shared(self):
        expected = self.output_file('library', mode='shared_library')
        result = self.builtin_dict['library']('library', ['main.cpp'],
                                              kind='shared')
        self.assertSameFile(result, expected, exclude={'post_install'})

        src = self.builtin_dict['source_file']('main.cpp')
        result = self.builtin_dict['library']('library', [src], kind='shared')
        self.assertSameFile(result, expected, exclude={'post_install'})

    def test_make_simple_static(self):
        expected = self.output_file('library', mode='static_library')
        result = self.builtin_dict['library']('library', ['main.cpp'],
                                              kind='static')
        self.assertSameFile(result, expected, exclude={'forward_opts'})

        src = self.builtin_dict['source_file']('main.cpp')
        result = self.builtin_dict['library']('library', [src], kind='static')
        self.assertSameFile(result, expected, exclude={'forward_opts'})

    def test_make_simple_dual(self):
        linker = self.env.builder('c++').linker('static_library')
        static_extra = {'forward_opts': {
            'compile_options': linker.forwarded_compile_options(
                AttrDict(name='liblibrary')
            ),
            'link_options': option_list(),
            'libs': [],
            'packages': [],
        }}

        src = self.builtin_dict['source_file']('main.cpp')
        with mock.patch('warnings.warn', lambda s: None):
            result = self.builtin_dict['library']('library', [src],
                                                  kind='dual')

        if self.env.builder('c++').can_dual_link:
            self.assertSameFile(result, file_types.DualUseLibrary(
                self.output_file('library', mode='shared_library'),
                self.output_file('library', mode='static_library',
                                 extra=static_extra)
            ), exclude={'post_install'})
        else:
            self.assertSameFile(result, self.output_file(
                'library', mode='shared_library'
            ))


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
        self.assertSameFile(link.whole_archive(self.builtin_dict, 'static'),
                            expected)

    def test_convert_from_static(self):
        lib = file_types.StaticLibrary(Path('static', Root.srcdir), None)
        result = self.builtin_dict['whole_archive'](lib)
        self.assertSameFile(result, file_types.WholeArchive(lib))

    def test_convert_from_static_invalid_args(self):
        lib = file_types.StaticLibrary(Path('static', Root.srcdir), None)
        self.assertRaises(TypeError, self.builtin_dict['whole_archive'], lib,
                          files=['foo.cpp'])
