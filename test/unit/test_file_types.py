from itertools import zip_longest

from . import *

from bfg9000 import iterutils
from bfg9000.file_types import *
from bfg9000.path import Path, Root


def pathfn(path, obj):
    return path.reroot()


class FileTest(TestCase):
    def assertSameFile(self, a, b):
        def diff_node(a, b, attr_path=()):
            diffs = []
            if type(a) is not type(b):
                diffs.append((attr_path, type(a), type(b)))
            elif iterutils.ismapping(a) and iterutils.ismapping(b):
                for i in sorted(set(a.keys()) | set(b.keys())):
                    curr_path = attr_path + (i,)
                    diffs.extend(diff_node(a.get(i), b.get(i), curr_path))
            elif iterutils.isiterable(a) and iterutils.isiterable(b):
                for i, (ai, bi) in enumerate(zip_longest(a, b)):
                    curr_path = attr_path + (i,)
                    diffs.extend(diff_node(ai, bi, curr_path))
            elif isinstance(a, Node) and isinstance(b, Node):
                seen_key = (id(a), id(b))
                if seen_key in seen:
                    return []
                seen.add(seen_key)

                for i in sorted(set(a.__dict__.keys()) |
                                set(b.__dict__.keys())):
                    curr_path = attr_path + (i,)
                    diffs.extend(diff_node(
                        getattr(a, i, None), getattr(b, i, None), curr_path
                    ))
            elif a != b:
                diffs.append((attr_path, a, b))

            return diffs

        seen = set()
        diffs = diff_node(a, b)
        if diffs:
            raise AssertionError('mismatched files:\n' + '\n'.join(
                '  {}: {!r} != {!r}'.format(
                    '.'.join(str(j) for j in i[0]), *i[1:]
                ) for i in diffs
            ))

    def assertClone(self, a, b, *, recursive=False):
        self.assertSameFile(a.clone(pathfn, recursive), b)


class TestNode(TestCase):
    def test_equality(self):
        self.assertTrue(Node('foo') == Node('foo'))
        self.assertFalse(Node('foo') != Node('foo'))

        self.assertFalse(Node('foo') == Node('bar'))
        self.assertTrue(Node('foo') != Node('bar'))


class TestFile(FileTest):
    def test_directory_path(self):
        self.assertRaises(ValueError, File, Path('foo/', Root.srcdir))

    def test_clone(self):
        self.assertClone(File(Path('a', Root.srcdir)),
                         File(Path('a')))


class TestDirectory(FileTest):
    def test_directory_path(self):
        d = Directory(Path('foo', Root.srcdir))
        self.assertTrue(d.path.directory)
        d = Directory(Path('foo/', Root.srcdir))
        self.assertTrue(d.path.directory)

    def test_clone(self):
        self.assertClone(Directory(Path('a', Root.srcdir)),
                         Directory(Path('a')))

        src = Directory(Path('a', Root.srcdir), [
            File(Path('a/b', Root.srcdir))
        ])
        dst = Directory(Path('a'), [File(Path('a/b', Root.srcdir))])
        self.assertClone(src, dst)

    def test_clone_recursive(self):
        self.assertClone(Directory(Path('a', Root.srcdir)),
                         Directory(Path('a')), recursive=True)

        src = Directory(Path('a', Root.srcdir), [
            File(Path('a/b', Root.srcdir))
        ])
        dst = Directory(Path('a'), [File(Path('a/b'))])
        self.assertClone(src, dst, recursive=True)


class TestSourceFile(FileTest):
    def test_clone(self):
        self.assertClone(SourceFile(Path('a', Root.srcdir), 'c'),
                         SourceFile(Path('a'), 'c'))

    def test_clone_recursive(self):
        self.assertClone(SourceFile(Path('a', Root.srcdir), 'c'),
                         SourceFile(Path('a'), 'c'), recursive=True)


class TestHeaderFile(FileTest):
    def test_clone(self):
        self.assertClone(HeaderFile(Path('a', Root.srcdir), 'c'),
                         HeaderFile(Path('a'), 'c'))

    def test_clone_recursive(self):
        self.assertClone(HeaderFile(Path('a', Root.srcdir), 'c'),
                         HeaderFile(Path('a'), 'c'), recursive=True)


class TestPrecompiledHeader(FileTest):
    def test_clone(self):
        self.assertClone(PrecompiledHeader(Path('a', Root.srcdir), 'c'),
                         PrecompiledHeader(Path('a'), 'c'))

    def test_clone_recursive(self):
        self.assertClone(PrecompiledHeader(Path('a', Root.srcdir), 'c'),
                         PrecompiledHeader(Path('a'), 'c'), recursive=True)


class TestMsvcPrecompiledHeader(FileTest):
    def test_clone(self):
        src = MsvcPrecompiledHeader(
            Path('a.h', Root.srcdir), Path('a.o', Root.srcdir),
            'a', 'elf', 'c'
        )
        dst = MsvcPrecompiledHeader(
            Path('a.h'), Path('a.o', Root.srcdir), 'a', 'elf', 'c'
        )
        dst.object_file.parent = src
        self.assertClone(src, dst)

        dst_obj = ObjectFile(Path('a.o'), 'elf', 'c', private=True)
        self.assertClone(src.object_file, dst_obj)

    def test_clone_recursive(self):
        src = MsvcPrecompiledHeader(
            Path('a.h', Root.srcdir), Path('a.o', Root.srcdir),
            'a', 'elf', 'c'
        )
        dst = MsvcPrecompiledHeader(Path('a.h'), Path('a.o'), 'a', 'elf', 'c')
        self.assertClone(src, dst, recursive=True)
        self.assertClone(src.object_file, dst.object_file, recursive=True)


class TestHeaderDirectory(FileTest):
    def test_clone(self):
        self.assertClone(HeaderDirectory(Path('a', Root.srcdir)),
                         HeaderDirectory(Path('a')))

        src = HeaderDirectory(Path('a', Root.srcdir), [
            HeaderFile(Path('a/b.h', Root.srcdir), 'c')
        ], True, 'c')
        dst = HeaderDirectory(Path('a'), [
            HeaderFile(Path('a/b.h', Root.srcdir), 'c')
        ], True, 'c')
        self.assertClone(src, dst)

    def test_clone_recursive(self):
        self.assertClone(HeaderDirectory(Path('a', Root.srcdir)),
                         HeaderDirectory(Path('a')),
                         recursive=True)

        src = HeaderDirectory(Path('a', Root.srcdir), [
            HeaderFile(Path('a/b.h', Root.srcdir), 'c')
        ], True, 'c')
        dst = HeaderDirectory(Path('a'), [
            HeaderFile(Path('a/b.h'), 'c')
        ], True, 'c')
        self.assertClone(src, dst, recursive=True)


class TestObjectFile(FileTest):
    def test_clone(self):
        self.assertClone(ObjectFile(Path('a', Root.srcdir), 'elf', 'c'),
                         ObjectFile(Path('a'), 'elf', 'c'))

    def test_clone_recursive(self):
        self.assertClone(ObjectFile(Path('a', Root.srcdir), 'elf', 'c'),
                         ObjectFile(Path('a'), 'elf', 'c'), recursive=True)


class TestExecutable(FileTest):
    def test_clone(self):
        self.assertClone(Executable(Path('a', Root.srcdir), 'elf', 'c'),
                         Executable(Path('a'), 'elf', 'c'))

    def test_clone_recursive(self):
        self.assertClone(Executable(Path('a', Root.srcdir), 'elf', 'c'),
                         Executable(Path('a'), 'elf', 'c'), recursive=True)


class TestSharedLibrary(FileTest):
    def test_clone(self):
        self.assertClone(SharedLibrary(Path('a', Root.srcdir), 'elf', 'c'),
                         SharedLibrary(Path('a'), 'elf', 'c'))

    def test_clone_recursive(self):
        self.assertClone(SharedLibrary(Path('a', Root.srcdir), 'elf', 'c'),
                         SharedLibrary(Path('a'), 'elf', 'c'), recursive=True)


class TestLinkLibrary(FileTest):
    def test_clone(self):
        lib = SharedLibrary(Path('a.so', Root.srcdir), 'elf', 'c')
        self.assertClone(LinkLibrary(Path('a', Root.srcdir), lib),
                         LinkLibrary(Path('a'), lib))

    def test_clone_recursive(self):
        srclib = SharedLibrary(Path('a.so', Root.srcdir), 'elf', 'c')
        dstlib = SharedLibrary(Path('a.so'), 'elf', 'c')
        self.assertClone(LinkLibrary(Path('a', Root.srcdir), srclib),
                         LinkLibrary(Path('a'), dstlib), recursive=True)


class TestVersionedSharedLibrary(FileTest):
    def test_clone(self):
        src = VersionedSharedLibrary(
            Path('a.1.2.3', Root.srcdir), 'elf', 'c',
            Path('a.1', Root.srcdir), Path('a', Root.srcdir)
        )
        dst = VersionedSharedLibrary(
            Path('a.1.2.3'), 'elf', 'c',
            Path('a.1', Root.srcdir), Path('a', Root.srcdir)
        )
        dst.soname.library = dst.soname.linktime_deps[0] = src
        dst.link.library = dst.link.linktime_deps[0] = src.soname
        dst.soname.parent = dst.link.parent = src
        self.assertClone(src, dst)

        dst_soname = LinkLibrary(Path('a.1'), src)
        self.assertClone(src.soname, dst_soname)

        dst_link = LinkLibrary(Path('a'), src.soname)
        self.assertClone(src.link, dst_link)

    def test_clone_recursive(self):
        src = VersionedSharedLibrary(
            Path('a.1.2.3', Root.srcdir), 'elf', 'c',
            Path('a.1', Root.srcdir), Path('a', Root.srcdir)
        )
        dst = VersionedSharedLibrary(
            Path('a.1.2.3'), 'elf', 'c', Path('a.1'), Path('a')
        )
        self.assertClone(src, dst, recursive=True)
        self.assertClone(src.soname, dst.soname, recursive=True)
        self.assertClone(src.link, dst.link, recursive=True)


class TestStaticLibrary(FileTest):
    def test_clone(self):
        self.assertClone(StaticLibrary(Path('a', Root.srcdir), 'elf', 'c'),
                         StaticLibrary(Path('a'), 'elf', 'c'))

        src = StaticLibrary(Path('a', Root.srcdir), 'elf', 'c', {'foo': 'bar'})
        dst = StaticLibrary(Path('a'), 'elf', 'c', {'foo': 'bar'})
        self.assertClone(src, dst)

    def test_clone_recursive(self):
        self.assertClone(StaticLibrary(Path('a', Root.srcdir), 'elf', 'c'),
                         StaticLibrary(Path('a'), 'elf', 'c'), recursive=True)

        src = StaticLibrary(Path('a', Root.srcdir), 'elf', 'c', {'foo': 'bar'})
        dst = StaticLibrary(Path('a'), 'elf', 'c', {'foo': 'bar'})
        self.assertClone(src, dst, recursive=True)


class TestExportFile(FileTest):
    def test_clone(self):
        self.assertClone(ExportFile(Path('a', Root.srcdir)),
                         ExportFile(Path('a')))

    def test_clone_recursive(self):
        self.assertClone(ExportFile(Path('a', Root.srcdir)),
                         ExportFile(Path('a')), recursive=True)


class TestDllBinary(FileTest):
    def test_clone(self):
        src = DllBinary(Path('a.dll', Root.srcdir), 'elf', 'c',
                        Path('a.lib', Root.srcdir))
        dst = DllBinary(Path('a.dll'), 'elf', 'c', Path('a.lib', Root.srcdir))
        dst.import_lib.library = dst.import_lib.linktime_deps[0] = src
        dst.import_lib.parent = src
        self.assertClone(src, dst)

        dst_import = LinkLibrary(Path('a.lib'), src)
        self.assertClone(src.import_lib, dst_import)

        src = DllBinary(Path('a.dll', Root.srcdir), 'elf', 'c',
                        Path('a.lib', Root.srcdir), Path('a.exp', Root.srcdir))
        dst = DllBinary(Path('a.dll'), 'elf', 'c', Path('a.lib', Root.srcdir),
                        Path('a.exp', Root.srcdir))
        dst.import_lib.library = dst.import_lib.linktime_deps[0] = src
        dst.import_lib.parent = dst.export_file.parent = src
        self.assertClone(src, dst)

        dst_import = LinkLibrary(Path('a.lib'), src)
        self.assertClone(src.import_lib, dst_import)

        dst_export = ExportFile(Path('a.exp'))
        self.assertClone(src.export_file, dst_export)

    def test_clone_recursive(self):
        src = DllBinary(Path('a.dll', Root.srcdir), 'elf', 'c',
                        Path('a.lib', Root.srcdir))
        dst = DllBinary(Path('a.dll'), 'elf', 'c', Path('a.lib'))
        self.assertClone(src, dst, recursive=True)
        self.assertClone(src.import_lib, dst.import_lib, recursive=True)

        src = DllBinary(Path('a.dll', Root.srcdir), 'elf', 'c',
                        Path('a.lib', Root.srcdir), Path('a.exp', Root.srcdir))
        dst = DllBinary(Path('a.dll'), 'elf', 'c',
                        Path('a.lib'), Path('a.exp'))
        self.assertClone(src, dst, recursive=True)
        self.assertClone(src.import_lib, dst.import_lib, recursive=True)
        self.assertClone(src.export_file, dst.export_file, recursive=True)


class TestDualUseLibrary(FileTest):
    def test_equality(self):
        shared_a = SharedLibrary(Path('shared_a'), 'elf')
        shared_b = SharedLibrary(Path('shared_b'), 'elf')
        static_a = SharedLibrary(Path('static_a'), 'elf')
        static_b = SharedLibrary(Path('static_b'), 'elf')

        Dual = DualUseLibrary

        self.assertTrue(Dual(shared_a, static_a) == Dual(shared_a, static_a))
        self.assertFalse(Dual(shared_a, static_a) != Dual(shared_a, static_a))

        self.assertFalse(Dual(shared_a, static_a) == Dual(shared_b, static_b))
        self.assertTrue(Dual(shared_a, static_a) != Dual(shared_b, static_b))

    def test_clone(self):
        shared_src = SharedLibrary(Path('shared', Root.srcdir), 'elf', 'c')
        static_src = StaticLibrary(Path('static', Root.srcdir), 'elf', 'c')
        shared_dst = SharedLibrary(Path('shared'), 'elf', 'c')
        static_dst = StaticLibrary(Path('static'), 'elf', 'c')
        dual_src = DualUseLibrary(shared_src, static_src)
        dual_dst = DualUseLibrary(shared_dst, static_dst)
        self.assertClone(dual_src, dual_dst)

        shared_dst.parent = None
        self.assertClone(shared_src, shared_dst)

    def test_clone_recursive(self):
        shared_src = VersionedSharedLibrary(
            Path('shared.1.2.3', Root.srcdir), 'elf', 'c',
            Path('shared.1', Root.srcdir), Path('shared', Root.srcdir)
        )
        static_src = StaticLibrary(Path('static', Root.srcdir), 'elf', 'c')
        dual_src = DualUseLibrary(shared_src, static_src)

        shared_dst = VersionedSharedLibrary(
            Path('shared.1.2.3'), 'elf', 'c',
            Path('shared.1'), Path('shared')
        )
        static_dst = StaticLibrary(Path('static'), 'elf', 'c')
        dual_dst = DualUseLibrary(shared_dst, static_dst)
        self.assertClone(dual_src, dual_dst, recursive=True)
        self.assertClone(shared_src, shared_dst, recursive=True)
        self.assertClone(shared_src.soname, shared_dst.soname, recursive=True)


class TestPkgConfigPcFile(FileTest):
    def test_clone(self):
        self.assertClone(PkgConfigPcFile(Path('a', Root.srcdir)),
                         PkgConfigPcFile(Path('a')))
