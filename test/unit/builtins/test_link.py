from unittest import mock

from .common import AlwaysEqual, AttrDict, BuiltinTest
from bfg9000.builtins import compile, default, link, packages, project  # noqa
from bfg9000 import file_types, options as opts
from bfg9000.environment import LibraryMode
from bfg9000.iterutils import listify, unlistify
from bfg9000.packages import CommonPackage
from bfg9000.path import Path, Root


class LinkTest(BuiltinTest):
    def output_file(self, name, step={}, lang='c++', mode=None, extra={}):
        linker = self.env.builder(lang).linker(mode or self.mode)
        step_args = {'langs': [lang]}
        step_args.update(step)
        step = AttrDict(**step_args)

        output = linker.output_file(name, step)
        public_output = linker.post_build(self.context, [], output, step)

        result = [i for i in listify(public_output or output) if not i.private]
        for i in result:
            for k, v in extra.items():
                setattr(i, k, v)
        return unlistify(result)

    def object_file(self, name, lang='c++'):
        compiler = self.env.builder(lang).compiler
        return compiler.output_file(name, None)


class TestExecutable(LinkTest):
    mode = 'executable'

    def test_identity(self):
        expected = file_types.Executable(Path('exe', Root.srcdir), None)
        self.assertIs(self.context['executable'](expected), expected)

    def test_src_file(self):
        expected = file_types.Executable(
            Path('exe', Root.srcdir),
            self.env.target_platform.object_format, 'c'
        )
        self.assertSameFile(self.context['executable']('exe'), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

        self.context['project'](lang='c++')
        expected.lang = 'c++'
        self.assertSameFile(self.context['executable']('exe'), expected)

    def test_no_dist(self):
        expected = file_types.Executable(
            Path('exe', Root.srcdir),
            self.env.target_platform.object_format, 'c'
        )
        self.assertSameFile(self.context['executable']('exe', dist=False),
                            expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile])

    def test_make_simple(self):
        result = self.context['executable']('exe', ['main.cpp'])
        self.assertSameFile(result, self.output_file('exe'))
        self.assertSameFile(result.creator.files[0],
                            self.object_file('exe.int/main'))

        result = self.context['executable'](name='exe', files=['main.cpp'])
        self.assertSameFile(result, self.output_file('exe'))

        src = self.context['source_file']('main.cpp')
        result = self.context['executable']('exe', [src])
        self.assertSameFile(result, self.output_file('exe'))

        obj = self.context['object_file']('main.o', lang='c++')
        result = self.context['executable']('exe', [obj])
        self.assertSameFile(result, self.output_file('exe'))

        self.context['project'](intermediate_dirs=False)
        result = self.context['executable']('exe', ['main.cpp'])
        self.assertSameFile(result, self.output_file('exe'))
        self.assertSameFile(result.creator.files[0], self.object_file('main'))

    def test_make_override_lang(self):
        expected = self.output_file('exe')

        src = self.context['source_file']('main.c', 'c')
        result = self.context['executable']('exe', [src], lang='c++')
        self.assertSameFile(result, expected)
        self.assertEqual(result.creator.langs, ['c++'])
        self.assertEqual(result.creator.linker.lang, 'c++')

        obj = self.context['object_file']('main.o', lang='c')
        result = self.context['executable']('exe', [obj], lang='c++')
        self.assertSameFile(result, expected)
        self.assertEqual(result.creator.langs, ['c'])
        self.assertEqual(result.creator.linker.lang, 'c++')

    def test_make_directory(self):
        executable = self.context['executable']
        result = executable('dir/exe', ['main.cpp'])
        self.assertSameFile(result, self.output_file('dir/exe'))
        self.assertSameFile(result.creator.files[0],
                            self.object_file('dir/exe.int/PAR/main'))

        result = executable('dir/exe', ['dir/main.cpp'])
        self.assertSameFile(result, self.output_file('dir/exe'))
        self.assertSameFile(result.creator.files[0],
                            self.object_file('dir/exe.int/main'))

        result = executable('exe', ['main.cpp'], intermediate_dir=None)
        self.assertSameFile(result, self.output_file('exe'))
        self.assertSameFile(result.creator.files[0], self.object_file('main'))

        result = executable('exe', ['main.cpp'], intermediate_dir='dir')
        self.assertSameFile(result, self.output_file('exe'))
        self.assertSameFile(result.creator.files[0],
                            self.object_file('dir/main'))

        self.context['project'](intermediate_dirs=False)
        result = executable('exe', ['main.cpp'], intermediate_dir='dir')
        self.assertSameFile(result, self.output_file('exe'))
        self.assertSameFile(result.creator.files[0],
                            self.object_file('dir/main'))

    def test_make_submodule(self):
        with self.context.push_path(Path('dir/build.bfg', Root.srcdir)):
            executable = self.context['executable']
            result = executable('exe', ['main.cpp'])
            self.assertSameFile(result, self.output_file('dir/exe'))
            self.assertSameFile(result.creator.files[0],
                                self.object_file('dir/exe.int/main'))

            result = executable('sub/exe', ['sub/main.cpp'])
            self.assertSameFile(result, self.output_file('dir/sub/exe'))
            self.assertSameFile(result.creator.files[0],
                                self.object_file('dir/sub/exe.int/main'))

            result = executable('exe', ['main.cpp'], intermediate_dir=None)
            self.assertSameFile(result, self.output_file('dir/exe'))
            self.assertSameFile(result.creator.files[0],
                                self.object_file('dir/main'))

    def test_lib_order(self):
        fmt = self.env.target_platform.object_format
        lib = opts.lib(file_types.SharedLibrary(Path('libfoo', Root.srcdir),
                                                fmt))
        pkg_libdir = opts.lib_dir(file_types.Directory(
            Path('/usr/lib', Root.absolute)
        ))
        pkg = CommonPackage('pkg', fmt, None, opts.option_list(pkg_libdir))

        result = self.context['executable']('exe', ['main.cpp'], libs='libfoo',
                                            packages=pkg)
        self.assertEqual(result.creator.options,
                         opts.option_list(lib, pkg_libdir))

    def test_invalid_type(self):
        src = self.context['source_file']('main.cpp')
        self.assertRaises(TypeError, self.context['executable'], src, [src])

    def test_make_no_files(self):
        self.assertRaises(ValueError, self.context['executable'], 'exe', [])

    def test_make_multiple_formats(self):
        obj1 = file_types.ObjectFile(Path('obj1.o', Root.srcdir), 'elf', 'c')
        obj2 = file_types.ObjectFile(Path('obj2.o', Root.srcdir), 'coff', 'c')
        self.assertRaises(ValueError, self.context['executable'], 'exe',
                          [obj1, obj2])

    def test_make_no_langs(self):
        obj1 = file_types.ObjectFile(Path('obj1.o', Root.srcdir), 'elf')
        obj2 = file_types.ObjectFile(Path('obj2.o', Root.srcdir), 'elf')
        self.assertRaises(ValueError, self.context['executable'], 'exe',
                          [obj1, obj2])

    def test_extra_deps(self):
        dep = self.context['generic_file']('dep.txt')
        result = self.context['executable']('exe', ['main.cpp'],
                                            extra_deps=[dep])
        self.assertSameFile(result, self.output_file('exe'))
        self.assertSameFile(result.creator.files[0],
                            self.object_file('exe.int/main'))
        self.assertEqual(result.creator.extra_deps, [dep])

    def test_description(self):
        result = self.context['executable']('exe', ['main.cpp'],
                                            description='my description')
        self.assertEqual(result.creator.description, 'my description')


class TestSharedLibrary(LinkTest):
    mode = 'shared_library'

    def test_identity(self):
        ex = file_types.SharedLibrary(Path('shared', Root.srcdir), None)
        self.assertIs(self.context['shared_library'](ex), ex)

    def test_src_file(self):
        expected = file_types.SharedLibrary(
            Path('shared', Root.srcdir),
            self.env.target_platform.object_format, 'c'
        )
        self.assertSameFile(self.context['shared_library']('shared'),
                            expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

        self.context['project'](lang='c++')
        expected.lang = 'c++'
        self.assertSameFile(self.context['shared_library']('shared'), expected)

    def test_no_dist(self):
        expected = file_types.SharedLibrary(
            Path('shared', Root.srcdir),
            self.env.target_platform.object_format, 'c'
        )
        self.assertSameFile(
            self.context['shared_library']('shared', dist=False), expected
        )
        self.assertEqual(list(self.build.sources()), [self.bfgfile])

    def test_convert_from_dual(self):
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        self.assertIs(self.context['shared_library'](lib), lib.shared)

    def test_convert_from_dual_invalid_args(self):
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        self.assertRaises(TypeError, self.context['shared_library'], lib,
                          files=['foo.cpp'])

    def test_make_simple(self):
        expected = self.output_file('shared')

        result = self.context['shared_library']('shared', ['main.cpp'])
        self.assertSameFile(result, expected, exclude={'post_install'})
        self.assertSameFile(result.creator.files[0],
                            self.object_file('libshared.int/main'))

        result = self.context['shared_library'](name='shared',
                                                files=['main.cpp'])
        self.assertSameFile(result, expected, exclude={'post_install'})

        src = self.context['source_file']('main.cpp')
        result = self.context['shared_library']('shared', [src])
        self.assertSameFile(result, expected, exclude={'post_install'})

        obj = self.context['object_file']('main.o', lang='c++')
        result = self.context['shared_library']('shared', [obj])
        self.assertSameFile(result, expected, exclude={'post_install'})

        self.context['project'](intermediate_dirs=False)
        result = self.context['shared_library']('shared', ['main.cpp'])
        self.assertSameFile(result, expected, exclude={'post_install'})
        self.assertSameFile(result.creator.files[0], self.object_file('main'))

    def test_make_soversion(self):
        src = self.context['source_file']('main.cpp')
        result = self.context['shared_library']('shared', [src], version='1',
                                                soversion='1')
        self.assertSameFile(result, self.output_file(
            'shared', step={'version': '1', 'soversion': '1'}
        ), exclude={'post_install'})

        self.assertRaises(ValueError, self.context['shared_library'], 'shared',
                          [src], version='1')
        self.assertRaises(ValueError, self.context['shared_library'], 'shared',
                          [src], soversion='1')

    def test_make_override_lang(self):
        shared_library = self.context['shared_library']
        expected = self.output_file('shared')

        src = self.context['source_file']('main.c', 'c')
        result = shared_library('shared', [src], lang='c++')
        self.assertSameFile(result, expected, exclude={'post_install'})
        self.assertEqual(result.creator.langs, ['c++'])
        self.assertEqual(result.creator.linker.lang, 'c++')

        obj = self.context['object_file']('main.o', lang='c')
        result = shared_library('shared', [obj], lang='c++')
        self.assertSameFile(result, expected, exclude={'post_install'})
        self.assertEqual(result.creator.langs, ['c'])
        self.assertEqual(result.creator.linker.lang, 'c++')

    def test_make_runtime_deps(self):
        shared_library = self.context['shared_library']
        libfoo = shared_library('foo', ['foo.cpp'])

        expected = self.output_file('shared')
        expected.runtime_file.runtime_deps = [libfoo.runtime_file]
        result = shared_library('shared', ['main.cpp'], libs=[libfoo])
        self.assertSameFile(result, expected, exclude={'post_install'})

    def test_make_directory(self):
        shared_library = self.context['shared_library']
        expected = self.output_file('dir/shared')

        result = shared_library('dir/shared', ['main.cpp'])
        self.assertSameFile(result, expected, exclude={'post_install'})
        self.assertSameFile(result.creator.files[0],
                            self.object_file('dir/libshared.int/PAR/main'))

        result = shared_library('dir/shared', ['dir/main.cpp'])
        self.assertSameFile(result, expected, exclude={'post_install'})
        self.assertSameFile(result.creator.files[0],
                            self.object_file('dir/libshared.int/main'))

        expected = self.output_file('shared')

        result = shared_library('shared', ['main.cpp'], intermediate_dir=None)
        self.assertSameFile(result, expected, exclude={'post_install'})
        self.assertSameFile(result.creator.files[0], self.object_file('main'))

        result = shared_library('shared', ['main.cpp'], intermediate_dir='dir')
        self.assertSameFile(result, expected, exclude={'post_install'})
        self.assertSameFile(result.creator.files[0],
                            self.object_file('dir/main'))

        self.context['project'](intermediate_dirs=False)
        result = shared_library('shared', ['main.cpp'], intermediate_dir='dir')
        self.assertSameFile(result, expected, exclude={'post_install'})
        self.assertSameFile(result.creator.files[0],
                            self.object_file('dir/main'))

    def test_lib_order(self):
        fmt = self.env.target_platform.object_format
        lib = opts.lib(file_types.SharedLibrary(Path('libfoo', Root.srcdir),
                                                fmt))
        pkg_libdir = opts.lib_dir(file_types.Directory(
            Path('/usr/lib', Root.absolute)
        ))
        pkg = CommonPackage('pkg', fmt, None, opts.option_list(pkg_libdir))

        result = self.context['shared_library']('shared', ['main.cpp'],
                                                libs='libfoo', packages=pkg)
        self.assertEqual(result.creator.options,
                         opts.option_list(lib, pkg_libdir))

    def test_invalid_type(self):
        src = self.context['source_file']('main.cpp')
        self.assertRaises(TypeError, self.context['shared_library'], src,
                          [src])

    def test_make_no_files(self):
        self.assertRaises(ValueError, self.context['shared_library'], 'shared',
                          [])

    def test_description(self):
        result = self.context['shared_library'](
            'shared', ['main.cpp'], description='my description'
        )
        self.assertEqual(result.creator.description, 'my description')

    def test_extra_deps(self):
        dep = self.context['generic_file']('dep.txt')
        expected = self.output_file('shared')

        result = self.context['shared_library']('shared', ['main.cpp'],
                                                extra_deps=[dep])
        self.assertSameFile(result, expected, exclude={'post_install'})
        self.assertSameFile(result.creator.files[0],
                            self.object_file('libshared.int/main'))
        self.assertEqual(result.creator.extra_deps, [dep])


class TestStaticLibrary(LinkTest):
    mode = 'static_library'

    def extra(self, name='libstatic', lang='c++', libs=[], **kwargs):
        linker = self.env.builder(lang).linker(self.mode)
        extra = {'forward_opts': opts.ForwardOptions(
            compile_options=linker.forwarded_compile_options(
                AttrDict(name=name)
            ),
            libs=libs,
        )}
        extra.update(kwargs)
        return extra

    def test_identity(self):
        ex = file_types.StaticLibrary(Path('static', Root.srcdir), None)
        self.assertIs(self.context['static_library'](ex), ex)

    def test_src_file(self):
        expected = file_types.StaticLibrary(
            Path('static', Root.srcdir),
            self.env.target_platform.object_format, 'c'
        )
        self.assertSameFile(self.context['static_library']('static'), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

        self.context['project'](lang='c++')
        expected.lang = 'c++'
        self.assertSameFile(self.context['static_library']('static'), expected)

    def test_no_dist(self):
        expected = file_types.StaticLibrary(
            Path('static', Root.srcdir),
            self.env.target_platform.object_format, 'c'
        )
        self.assertSameFile(
            self.context['static_library']('static', dist=False), expected
        )
        self.assertEqual(list(self.build.sources()), [self.bfgfile])

    def test_convert_from_dual(self):
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        self.assertIs(self.context['static_library'](lib), lib.static)

    def test_convert_from_dual_invalid_args(self):
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        self.assertRaises(TypeError, self.context['static_library'], lib,
                          files=['foo.cpp'])

    def test_make_simple(self):
        expected = self.output_file('static', extra=self.extra())

        result = self.context['static_library']('static', ['main.cpp'])
        self.assertSameFile(result, expected)
        self.assertSameFile(result.creator.files[0],
                            self.object_file('libstatic.int/main'))

        result = self.context['static_library'](name='static',
                                                files=['main.cpp'])
        self.assertSameFile(result, expected)

        src = self.context['source_file']('main.cpp')
        result = self.context['static_library']('static', [src])
        self.assertSameFile(result, expected)

        obj = self.context['object_file']('main.o', lang='c++')
        result = self.context['static_library']('static', [obj])
        self.assertSameFile(result, expected)

        self.context['project'](intermediate_dirs=False)
        result = self.context['static_library']('static', ['main.cpp'])
        self.assertSameFile(result, expected)
        self.assertSameFile(result.creator.files[0], self.object_file('main'))

    def test_make_override_lang(self):
        static_library = self.context['static_library']

        src = self.context['source_file']('main.c', 'c')
        result = static_library('static', [src], lang='c++')
        self.assertSameFile(result, self.output_file(
            'static', extra=self.extra()
        ))
        self.assertEqual(result.creator.langs, ['c++'])
        self.assertEqual(result.creator.linker.lang, 'c++')

        obj = self.context['object_file']('main.o', lang='c')
        result = static_library('static', [obj], lang='c++')
        self.assertSameFile(result, self.output_file(
            'static', lang='c', extra=self.extra(lang='c')
        ))
        self.assertEqual(result.creator.langs, ['c'])
        self.assertEqual(result.creator.linker.lang, 'c++')

    def test_make_linktime_deps(self):
        static_library = self.context['static_library']
        libfoo = static_library('libfoo.a')

        result = static_library('static', ['main.c'], libs=[libfoo])
        self.assertSameFile(result, self.output_file(
            'static', lang='c',
            extra=self.extra(lang='c', libs=[libfoo], linktime_deps=[libfoo])
        ))

    def test_make_directory(self):
        static_library = self.context['static_library']
        expected = self.output_file('dir/static',
                                    extra=self.extra('dir/libstatic'))

        result = static_library('dir/static', ['main.cpp'])
        self.assertSameFile(result, expected)
        self.assertSameFile(result.creator.files[0],
                            self.object_file('dir/libstatic.int/PAR/main'))

        result = static_library('dir/static', ['dir/main.cpp'])
        self.assertSameFile(result, expected)
        self.assertSameFile(result.creator.files[0],
                            self.object_file('dir/libstatic.int/main'))

        expected = self.output_file('static', extra=self.extra())

        result = static_library('static', ['main.cpp'], intermediate_dir=None)
        self.assertSameFile(result, expected)
        self.assertSameFile(result.creator.files[0], self.object_file('main'))

        result = static_library('static', ['main.cpp'], intermediate_dir='dir')
        self.assertSameFile(result, expected)
        self.assertSameFile(result.creator.files[0],
                            self.object_file('dir/main'))

        self.context['project'](intermediate_dirs=False)
        result = static_library('static', ['main.cpp'], intermediate_dir='dir')
        self.assertSameFile(result, expected)
        self.assertSameFile(result.creator.files[0],
                            self.object_file('dir/main'))

    def test_invalid_type(self):
        src = self.context['source_file']('main.cpp')
        self.assertRaises(TypeError, self.context['static_library'], src,
                          [src])

    def test_make_no_files(self):
        self.assertRaises(ValueError, self.context['static_library'], 'static',
                          [])

    def test_description(self):
        result = self.context['static_library'](
            'static', ['main.cpp'], description='my description'
        )
        self.assertEqual(result.creator.description, 'my description')

    def test_extra_deps(self):
        dep = self.context['generic_file']('dep.txt')
        expected = self.output_file('static', extra=self.extra())

        result = self.context['static_library']('static', ['main.cpp'],
                                                extra_deps=[dep])
        self.assertSameFile(result, expected)
        self.assertSameFile(result.creator.files[0],
                            self.object_file('libstatic.int/main'))
        self.assertEqual(result.creator.extra_deps, [dep])


class TestLibrary(LinkTest):
    def test_identity(self):
        self.env.library_mode = LibraryMode(True, True)
        expected = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        self.assertIs(self.context['library'](expected), expected)

    def test_convert_to_shared(self):
        self.env.library_mode = LibraryMode(True, False)
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        self.assertEqual(self.context['library'](lib), lib.shared)

    def test_convert_to_static(self):
        self.env.library_mode = LibraryMode(False, True)
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        self.assertEqual(self.context['library'](lib), lib.static)

    def test_convert_invalid_args(self):
        self.env.library_mode = LibraryMode(False, True)
        lib = file_types.DualUseLibrary(
            file_types.SharedLibrary(Path('shared', Root.srcdir), None),
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        self.assertRaises(TypeError, self.context['library'], lib,
                          files=['foo.cpp'])

    def test_no_library(self):
        self.env.library_mode = LibraryMode(False, False)
        self.assertRaises(ValueError, self.context['library'], 'library',
                          files=['foo.cpp'])

    def test_src_file(self):
        self.env.library_mode = LibraryMode(True, True)
        expected = file_types.StaticLibrary(
            Path('library', Root.srcdir),
            self.env.target_platform.object_format, 'c'
        )
        self.assertSameFile(self.context['library']('library'), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

        self.context['project'](lang='c++')
        expected.lang = 'c++'
        self.assertSameFile(self.context['library']('library'), expected)

    def test_src_file_explicit_static(self):
        expected = file_types.StaticLibrary(
            Path('library', Root.srcdir),
            self.env.target_platform.object_format, 'c'
        )
        self.assertSameFile(self.context['library']('library', kind='static'),
                            expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

        self.context['project'](lang='c++')
        expected.lang = 'c++'
        self.assertSameFile(self.context['library']('library', kind='static'),
                            expected)

    def test_src_file_explicit_shared(self):
        expected = file_types.SharedLibrary(
            Path('library', Root.srcdir),
            self.env.target_platform.object_format, 'c'
        )
        self.assertSameFile(self.context['library']('library', kind='shared'),
                            expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

        self.context['project'](lang='c++')
        expected.lang = 'c++'
        self.assertSameFile(self.context['library']('library', kind='shared'),
                            expected)

    def test_src_file_explicit_dual(self):
        self.assertRaises(ValueError, self.context['library'], 'library',
                          kind='dual')

    def test_no_dist(self):
        expected = file_types.SharedLibrary(
            Path('shared', Root.srcdir),
            self.env.target_platform.object_format, 'c'
        )
        self.assertSameFile(
            self.context['library']('shared', kind='shared', dist=False),
            expected
        )
        self.assertEqual(list(self.build.sources()), [self.bfgfile])

    def test_make_simple_shared(self):
        expected = self.output_file('library', mode='shared_library')
        result = self.context['library']('library', ['main.cpp'],
                                         kind='shared')
        self.assertSameFile(result, expected, exclude={'post_install'})
        self.assertSameFile(result.creator.files[0],
                            self.object_file('liblibrary.int/main'))

        src = self.context['source_file']('main.cpp')
        result = self.context['library']('library', [src], kind='shared')
        self.assertSameFile(result, expected, exclude={'post_install'})

    def test_make_simple_static(self):
        expected = self.output_file('library', mode='static_library')
        result = self.context['library']('library', ['main.cpp'],
                                         kind='static')
        self.assertSameFile(result, expected, exclude={'forward_opts'})
        self.assertSameFile(result.creator.files[0],
                            self.object_file('liblibrary.int/main'))

        src = self.context['source_file']('main.cpp')
        result = self.context['library']('library', [src], kind='static')
        self.assertSameFile(result, expected, exclude={'forward_opts'})

    def test_make_simple_dual(self):
        linker = self.env.builder('c++').linker('static_library')
        static_extra = {'forward_opts': opts.ForwardOptions(
            compile_options=linker.forwarded_compile_options(
                AttrDict(name='liblibrary')
            )
        )}

        src = self.context['source_file']('main.cpp')
        with mock.patch('warnings.warn', lambda s: None):
            result = self.context['library']('library', [src], kind='dual')

        if self.env.builder('c++').can_dual_link:
            self.assertSameFile(result, file_types.DualUseLibrary(
                self.output_file('library', mode='shared_library'),
                self.output_file('library', mode='static_library',
                                 extra=static_extra)
            ), exclude={'post_install'})
            for i in result.all:
                self.assertSameFile(i.creator.files[0],
                                    self.object_file('liblibrary.int/main'))
        else:
            self.assertSameFile(result, self.output_file(
                'library', mode='shared_library'
            ))
            self.assertSameFile(result.creator.files[0],
                                self.object_file('liblibrary.int/main'))

    def test_make_directory(self):
        library = self.context['library']
        expected = self.output_file('dir/library', mode='shared_library')

        result = library('dir/library', ['main.cpp'], kind='shared')
        self.assertSameFile(result, expected, exclude={'post_install'})
        self.assertSameFile(result.creator.files[0],
                            self.object_file('dir/liblibrary.int/PAR/main'))

        result = library('dir/library', ['dir/main.cpp'], kind='shared')
        self.assertSameFile(result, expected, exclude={'post_install'})
        self.assertSameFile(result.creator.files[0],
                            self.object_file('dir/liblibrary.int/main'))

        expected = self.output_file('library', mode='shared_library')

        result = library('library', ['main.cpp'], kind='shared',
                         intermediate_dir=None)
        self.assertSameFile(result, expected, exclude={'post_install'})
        self.assertSameFile(result.creator.files[0], self.object_file('main'))

        result = library('library', ['main.cpp'], kind='shared',
                         intermediate_dir='dir')
        self.assertSameFile(result, expected, exclude={'post_install'})
        self.assertSameFile(result.creator.files[0],
                            self.object_file('dir/main'))

        self.context['project'](intermediate_dirs=False)
        result = library('library', ['main.cpp'], kind='shared',
                         intermediate_dir='dir')
        self.assertSameFile(result, expected, exclude={'post_install'})
        self.assertSameFile(result.creator.files[0],
                            self.object_file('dir/main'))

    def test_extra_deps(self):
        # Shared
        dep = self.context['generic_file']('dep.txt')
        expected = self.output_file('library', mode='shared_library')
        result = self.context['library']('library', ['main.cpp'],
                                         kind='shared', extra_deps=[dep])
        self.assertSameFile(result, expected, exclude={'post_install'})
        self.assertSameFile(result.creator.files[0],
                            self.object_file('liblibrary.int/main'))
        self.assertEqual(result.creator.extra_deps, [dep])

        # Static
        expected = self.output_file('library', mode='static_library')
        result = self.context['library']('library', ['main.cpp'],
                                         kind='static', extra_deps=[dep])
        self.assertSameFile(result, expected, exclude={'forward_opts'})
        self.assertSameFile(result.creator.files[0],
                            self.object_file('liblibrary.int/main'))
        self.assertEqual(result.creator.extra_deps, [dep])

        # Dual
        with mock.patch('warnings.warn', lambda s: None):
            result = self.context['library']('library', ['main.cpp'],
                                             kind='dual', extra_deps=[dep])

        if self.env.builder('c++').can_dual_link:
            for i in result.all:
                self.assertEqual(i.creator.extra_deps, [dep])
        else:
            self.assertEqual(result.creator.extra_deps, [dep])


class TestWholeArchive(BuiltinTest):
    def test_identity(self):
        expected = file_types.WholeArchive(
            file_types.StaticLibrary(Path('static', Root.srcdir), None)
        )
        self.assertIs(self.context['whole_archive'](expected), expected)

    def test_src_file(self):
        expected = file_types.WholeArchive(
            file_types.StaticLibrary(
                Path('static', Root.srcdir),
                self.env.target_platform.object_format, 'c'
            )
        )
        self.assertSameFile(link.whole_archive(self.context, 'static'),
                            expected)

    def test_convert_from_static(self):
        lib = file_types.StaticLibrary(Path('static', Root.srcdir), None)
        result = self.context['whole_archive'](lib)
        self.assertSameFile(result, file_types.WholeArchive(lib))

    def test_convert_from_static_invalid_args(self):
        lib = file_types.StaticLibrary(Path('static', Root.srcdir), None)
        self.assertRaises(TypeError, self.context['whole_archive'], lib,
                          files=['foo.cpp'])


class TestMakeBackend(BuiltinTest):
    def test_simple(self):
        makefile = mock.Mock()
        obj = self.context['object_file']('main.o')

        result = self.context['executable']('exe', obj)
        link.make_link(result.creator, self.build, makefile, self.env)
        makefile.rule.assert_called_once_with(
            result, [obj], [], AlwaysEqual(), {}, None
        )

    def test_dir_sentinel(self):
        makefile = mock.Mock()
        obj = self.context['object_file']('main.o')

        result = self.context['executable']('dir/exe', obj)
        link.make_link(result.creator, self.build, makefile, self.env)
        makefile.rule.assert_called_once_with(
            result, [obj], [Path('dir/.dir')], AlwaysEqual(), {}, None
        )

    def test_extra_deps(self):
        makefile = mock.Mock()
        dep = self.context['generic_file']('dep.txt')
        obj = self.context['object_file']('main.o')

        result = self.context['executable']('exe', obj, extra_deps=dep)
        link.make_link(result.creator, self.build, makefile, self.env)
        makefile.rule.assert_called_once_with(
            result, [obj, dep], [], AlwaysEqual(), {}, None
        )


class TestNinjaBackend(BuiltinTest):
    def test_simple(self):
        ninjafile = mock.Mock()
        obj = self.context['object_file']('main.o')

        result = self.context['executable']('exe', obj)
        link.ninja_link(result.creator, self.build, ninjafile, self.env)
        ninjafile.build.assert_called_once_with(
            output=[result], rule='cc_link', inputs=[obj], implicit=[],
            variables={}
        )

    def test_extra_deps(self):
        ninjafile = mock.Mock()
        dep = self.context['generic_file']('dep.txt')
        obj = self.context['object_file']('main.o')

        result = self.context['executable']('exe', obj, extra_deps=dep)
        link.ninja_link(result.creator, self.build, ninjafile, self.env)
        ninjafile.build.assert_called_once_with(
            output=[result], rule='cc_link', inputs=[obj], implicit=[dep],
            variables={}
        )
