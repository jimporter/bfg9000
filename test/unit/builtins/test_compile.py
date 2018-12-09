import mock
from collections import namedtuple

from .common import BuiltinTest
from bfg9000.builtins import compile  # noqa
from bfg9000 import file_types
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
        obj = file_types.ObjectFile(Path('object', Root.srcdir), None)
        result = self.builtin_dict['object_file'](obj)
        self.assertEqual(result, obj)

    def test_src_file(self):
        result = self.builtin_dict['object_file']('object')
        self.assertEqual(result, file_types.ObjectFile(
            Path('object', Root.srcdir), None
        ))

    def test_make_simple(self):
        compiler = self.env.builder('c++').compiler

        result = self.builtin_dict['object_file'](file='main.cpp')
        self.assertEqual(result, self.output_file(compiler, 'main', None))

        result = self.builtin_dict['object_file']('object', 'main.cpp')
        self.assertEqual(result, self.output_file(compiler, 'object', None))

        src = file_types.SourceFile(Path('main.cpp', Root.srcdir))
        result = self.builtin_dict['object_file']('object', src)
        self.assertEqual(result, self.output_file(compiler, 'object', None))

    def test_make_no_lang(self):
        compiler = self.env.builder('c++').compiler

        result = self.builtin_dict['object_file']('object', 'main.goofy',
                                                  lang='c++')
        self.assertEqual(result, self.output_file(compiler, 'object', None))

        self.assertRaises(ValueError, self.builtin_dict['object_file'],
                          'object', 'main.goofy')

        src = file_types.SourceFile(Path('main.goofy', Root.srcdir))
        self.assertRaises(ValueError, self.builtin_dict['object_file'],
                          'object', src)

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
        pch_source = file_types.SourceFile(Path('file.cpp', Root.srcdir))

    def test_identity(self):
        obj = file_types.PrecompiledHeader(Path('header', Root.srcdir), None)
        result = self.builtin_dict['precompiled_header'](obj)
        self.assertEqual(result, obj)

    def test_src_file(self):
        result = self.builtin_dict['precompiled_header']('header')
        self.assertEqual(result, file_types.PrecompiledHeader(
            Path('header', Root.srcdir), None
        ))

    def test_make_simple(self):
        with mock.patch('bfg9000.builtins.file_types.generated_file',
                        return_value=self.MockFile()):
            compiler = self.env.builder('c++').pch_compiler
            pch = self.builtin_dict['precompiled_header']

            result = pch(file='main.hpp')
            self.assertEqual(result, self.output_file(compiler, 'main.hpp',
                                                      self.Context()))

            result = pch('object', 'main.hpp')
            self.assertEqual(result, self.output_file(compiler, 'object',
                                                      self.Context()))

            src = file_types.HeaderFile(Path('main.hpp', Root.srcdir))
            result = pch('object', src)
            self.assertEqual(result, self.output_file(compiler, 'object',
                                                      self.Context()))

    def test_make_no_lang(self):
        with mock.patch('bfg9000.builtins.file_types.generated_file',
                        return_value=self.MockFile()):
            compiler = self.env.builder('c++').pch_compiler
            pch = self.builtin_dict['precompiled_header']

            result = pch('object', 'main.goofy', lang='c++')
            self.assertEqual(result, self.output_file(compiler, 'object',
                                                      self.Context()))
            self.assertRaises(ValueError, pch, 'object', 'main.goofy')

            src = file_types.HeaderFile(Path('main.goofy', Root.srcdir))
            self.assertRaises(ValueError, pch, 'object', src)

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
