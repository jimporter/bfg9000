import mock
from collections import namedtuple

from .common import BuiltinTest
from bfg9000 import file_types
from bfg9000.builtins import compile  # noqa
from bfg9000.environment import LibraryMode
from bfg9000.iterutils import listify, unlistify
from bfg9000.path import Path, Root

MockCompile = namedtuple('MockCompile', ['file'])


class CompileTest(BuiltinTest):
    def output_file(self, compiler, name, context):
        output = compiler.output_file(name, context)
        public_output = compiler.post_build(self.build, [], output, context)
        return unlistify([i for i in listify(public_output or output)
                          if not i.private])


class TestObjectFile(CompileTest):
    def test_identity(self):
        expected = file_types.ObjectFile(Path('object', Root.srcdir), None)
        self.assertIs(self.builtin_dict['object_file'](expected), expected)

    def test_src_file(self):
        expected = file_types.ObjectFile(
            Path('object', Root.srcdir),
            self.env.target_platform.object_format, 'c'
        )
        self.assertSame(self.builtin_dict['object_file']('object'), expected)

    def test_make_simple(self):
        compiler = self.env.builder('c++').compiler

        result = self.builtin_dict['object_file'](file='main.cpp')
        self.assertSame(result, self.output_file(compiler, 'main', None),
                        exclude={'creator'})

        result = self.builtin_dict['object_file']('object', 'main.cpp')
        self.assertSame(result, self.output_file(compiler, 'object', None),
                        exclude={'creator'})

        src = self.builtin_dict['source_file']('main.cpp')
        result = self.builtin_dict['object_file']('object', src)
        self.assertSame(result, self.output_file(compiler, 'object', None),
                        exclude={'creator'})

    def test_make_no_lang(self):
        compiler = self.env.builder('c++').compiler

        result = self.builtin_dict['object_file']('object', 'main.goofy',
                                                  lang='c++')
        self.assertSame(result, self.output_file(compiler, 'object', None),
                        exclude={'creator'})

        self.assertRaises(ValueError, self.builtin_dict['object_file'],
                          'object', 'main.goofy')

        src = self.builtin_dict['source_file']('main.goofy')
        self.assertRaises(ValueError, self.builtin_dict['object_file'],
                          'object', src)

    def test_make_override_lang(self):
        compiler = self.env.builder('c++').compiler

        src = self.builtin_dict['source_file']('main.c', 'c')
        result = self.builtin_dict['object_file']('object', src, lang='c++')
        self.assertSame(result, self.output_file(compiler, 'object', None),
                        exclude={'creator'})
        self.assertEqual(result.creator.compiler.lang, 'c++')

    def test_includes(self):
        object_file = self.builtin_dict['object_file']

        result = object_file(file='main.cpp', includes='include')
        self.assertEqual(result.creator.includes, [
            file_types.HeaderDirectory(Path('include', Root.srcdir))
        ])

        hdr = self.builtin_dict['header_file']('include/main.hpp')
        result = object_file(file='main.cpp', includes=hdr)
        self.assertEqual(result.creator.includes, [
            file_types.HeaderDirectory(Path('include', Root.srcdir))
        ])

    def test_libs(self):
        self.env.library_mode = LibraryMode(True, False)

        result = self.builtin_dict['object_file'](file='main.java', libs='lib')
        self.assertEqual(result.creator.libs, [
            file_types.StaticLibrary(Path('lib', Root.srcdir), 'java')
        ])

    def test_pch(self):
        pch = file_types.PrecompiledHeader(Path('pch', Root.builddir), 'c')
        pch.object_file = 'foo'

        result = self.builtin_dict['object_file'](file='main.cpp', pch=pch)
        self.assertIs(result.creator.pch, pch)

        self.assertRaises(TypeError, self.builtin_dict['object_file'],
                          file='main.java', pch=pch)

    def test_make_no_name_or_file(self):
        self.assertRaises(TypeError, self.builtin_dict['object_file'])

    def test_description(self):
        result = self.builtin_dict['object_file'](
            file='main.cpp', description='my description'
        )
        self.assertEqual(result.creator.description, 'my description')


class TestPrecompiledHeader(CompileTest):
    class MockFile(object):
        def write(self, data):
            pass

    class Context(object):
        pch_source = file_types.SourceFile(Path('main.cpp', Root.srcdir),
                                           'c++')

    def test_identity(self):
        ex = file_types.PrecompiledHeader(Path('header', Root.srcdir), None)
        self.assertIs(self.builtin_dict['precompiled_header'](ex), ex)

    def test_src_file(self):
        expected = file_types.PrecompiledHeader(
            Path('header', Root.srcdir), 'c'
        )
        self.assertSame(self.builtin_dict['precompiled_header']('header'),
                        expected)

    def test_make_simple(self):
        with mock.patch('bfg9000.builtins.file_types.generated_file',
                        return_value=self.MockFile()):
            compiler = self.env.builder('c++').pch_compiler
            pch = self.builtin_dict['precompiled_header']

            result = pch(file='main.hpp')
            self.assertSame(result, self.output_file(
                compiler, 'main.hpp', self.Context()
            ), exclude={'creator'})

            result = pch('object', 'main.hpp')
            self.assertSame(result, self.output_file(
                compiler, 'object', self.Context()
            ), exclude={'creator'})

            src = self.builtin_dict['header_file']('main.hpp')
            result = pch('object', src)
            self.assertSame(result, self.output_file(
                compiler, 'object', self.Context()
            ), exclude={'creator'})

    def test_make_no_lang(self):
        with mock.patch('bfg9000.builtins.file_types.generated_file',
                        return_value=self.MockFile()):
            compiler = self.env.builder('c++').pch_compiler
            pch = self.builtin_dict['precompiled_header']

            result = pch('object', 'main.goofy', lang='c++')
            self.assertSame(result, self.output_file(
                compiler, 'object', self.Context()
            ), exclude={'creator'})
            self.assertRaises(ValueError, pch, 'object', 'main.goofy')

            src = self.builtin_dict['header_file']('main.goofy')
            self.assertRaises(ValueError, pch, 'object', src)

    def test_make_override_lang(self):
        with mock.patch('bfg9000.builtins.file_types.generated_file',
                        return_value=self.MockFile()):
            compiler = self.env.builder('c++').pch_compiler
            pch = self.builtin_dict['precompiled_header']

            src = self.builtin_dict['header_file']('main.h', 'c')
            result = pch('object', src, lang='c++')
            self.assertSame(result, self.output_file(
                compiler, 'object', self.Context()
            ), exclude={'creator'})
            self.assertEqual(result.creator.compiler.lang, 'c++')

    def test_make_no_name_or_file(self):
        self.assertRaises(TypeError, self.builtin_dict['precompiled_header'])

    def test_description(self):
        result = self.builtin_dict['precompiled_header'](
            file='main.hpp', description='my description'
        )
        self.assertEqual(result.creator.description, 'my description')


class TestObjectFiles(BuiltinTest):
    def make_object_files(self, make_src=False):
        files = [file_types.ObjectFile(Path(i, Root.srcdir), None)
                 for i in ['obj1', 'obj2']]
        if make_src:
            src_files = [file_types.SourceFile(Path(i, Root.srcdir), None)
                         for i in ['src1', 'src2']]
            for f, s in zip(files, src_files):
                f.creator = MockCompile(s)

        obj_files = self.builtin_dict['object_files'](files)

        if make_src:
            return obj_files, files, src_files
        return obj_files, files

    def test_initialize(self):
        obj_files, files = self.make_object_files()
        self.assertEqual(list(obj_files), files)

    def test_getitem_index(self):
        obj_files, files = self.make_object_files()
        self.assertEqual(obj_files[0], files[0])

    def test_getitem_string(self):
        obj_files, files, src_files = self.make_object_files(True)
        self.assertEqual(obj_files['src1'], files[0])

    def test_getitem_path(self):
        obj_files, files, src_files = self.make_object_files(True)
        self.assertEqual(obj_files[src_files[0].path], files[0])

    def test_getitem_file(self):
        obj_files, files, src_files = self.make_object_files(True)
        self.assertEqual(obj_files[src_files[0]], files[0])

    def test_getitem_not_found(self):
        obj_files, files, src_files = self.make_object_files(True)
        self.assertRaises(IndexError, lambda: obj_files[2])
        self.assertRaises(IndexError, lambda: obj_files['src3'])
        self.assertRaises(IndexError, lambda: obj_files[Path(
            'src3', Root.srcdir
        )])
