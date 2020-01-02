from . import *

from bfg9000.file_types import *
from bfg9000.path import Path, Root


def pathfn(file):
    return file.path.reroot()


class FileTest(TestCase):
    def assertSameFile(self, a, b, extra=set(), seen=None):
        if seen is None:
            seen = set()
        seen.add(id(a))

        self.assertEqual(type(a), type(b))
        keys = ((set(a.__dict__.keys()) | set(b.__dict__.keys())) -
                getattr(a, '_clone_exclude', set())) | {'path'} | extra

        for i in keys:
            ai, bi = getattr(a, i, None), getattr(b, i, None)
            if isinstance(ai, Node) and isinstance(bi, Node):
                if not id(ai) in seen:
                    self.assertSameFile(ai, bi, extra, seen)
            else:
                self.assertEqual(
                    ai, bi, '{!r}: {!r} != {!r}'.format(i, ai, bi)
                )

    def assertClone(self, a, b, recursive=False, extra=set()):
        self.assertSameFile(a.clone(pathfn, recursive), b, extra)


class TestNode(TestCase):
    def test_equality(self):
        self.assertTrue(Node('foo') == Node('foo'))
        self.assertFalse(Node('foo') != Node('foo'))

        self.assertFalse(Node('foo') == Node('bar'))
        self.assertTrue(Node('foo') != Node('bar'))


class TestFile(FileTest):
    def test_clone(self):
        self.assertClone(File(Path('a', Root.srcdir)),
                         File(Path('a')))


class TestDirectory(FileTest):
    def test_clone(self):
        self.assertClone(Directory(Path('a', Root.srcdir)),
                         Directory(Path('a')), extra={'files'})
        self.assertClone(
            Directory(Path('a', Root.srcdir), [
                File(Path('a/b', Root.srcdir))
            ]),
            Directory(Path('a'), [
                File(Path('a/b', Root.srcdir))
            ]),
            extra={'files'}
        )

    def test_clone_recursive(self):
        self.assertClone(Directory(Path('a', Root.srcdir)),
                         Directory(Path('a')), recursive=True, extra={'files'})
        self.assertClone(
            Directory(Path('a', Root.srcdir), [
                File(Path('a/b', Root.srcdir))
            ]),
            Directory(Path('a'), [File(Path('a/b'))]),
            recursive=True, extra={'files'}
        )


class TestResourceFile(FileTest):
    def test_clone(self):
        self.assertClone(ResourceFile(Path('a', Root.srcdir), 'c'),
                         ResourceFile(Path('a'), 'c'))


class TestSourceFile(FileTest):
    def test_clone(self):
        self.assertClone(SourceFile(Path('a', Root.srcdir), 'c'),
                         SourceFile(Path('a'), 'c'))


class TestHeaderFile(FileTest):
    def test_clone(self):
        self.assertClone(HeaderFile(Path('a', Root.srcdir), 'c'),
                         HeaderFile(Path('a'), 'c'))


class TestPrecompiledHeader(FileTest):
    def test_clone(self):
        self.assertClone(PrecompiledHeader(Path('a', Root.srcdir), 'c'),
                         PrecompiledHeader(Path('a'), 'c'))


class TestMsvcPrecompiledHeader(FileTest):
    def test_clone(self):
        self.assertClone(
            MsvcPrecompiledHeader(
                Path('a.h', Root.srcdir), Path('a.o', Root.srcdir), 'a', 'elf',
                'c'
            ),
            MsvcPrecompiledHeader(
                Path('a.h'), Path('a.o', Root.srcdir), 'a', 'elf', 'c'
            )
        )

    def test_clone_recursive(self):
        self.assertClone(
            MsvcPrecompiledHeader(
                Path('a.h', Root.srcdir), Path('a.o', Root.srcdir), 'a',
                'elf', 'c'
            ),
            MsvcPrecompiledHeader(Path('a.h'), Path('a.o'), 'a', 'elf', 'c'),
            recursive=True
        )


class TestHeaderDirectory(FileTest):
    def test_clone(self):
        self.assertClone(HeaderDirectory(Path('a', Root.srcdir)),
                         HeaderDirectory(Path('a')), extra={'files'})
        self.assertClone(
            HeaderDirectory(Path('a', Root.srcdir), [
                HeaderFile(Path('a/b.h', Root.srcdir), 'c')
            ], True, 'c'),
            HeaderDirectory(Path('a'), [
                HeaderFile(Path('a/b.h', Root.srcdir), 'c')
            ], True, 'c'),
            extra={'files'}
        )

    def test_clone_recursive(self):
        self.assertClone(HeaderDirectory(Path('a', Root.srcdir)),
                         HeaderDirectory(Path('a')),
                         recursive=True, extra={'files'})
        self.assertClone(
            HeaderDirectory(Path('a', Root.srcdir), [
                HeaderFile(Path('a/b.h', Root.srcdir), 'c')
            ], True, 'c'),
            HeaderDirectory(Path('a'), [
                HeaderFile(Path('a/b.h'), 'c')
            ], True, 'c'),
            recursive=True, extra={'files'}
        )


class TestObjectFile(FileTest):
    def test_clone(self):
        self.assertClone(ObjectFile(Path('a', Root.srcdir), 'elf', 'c'),
                         ObjectFile(Path('a'), 'elf', 'c'))


class TestExecutable(FileTest):
    def test_clone(self):
        self.assertClone(Executable(Path('a', Root.srcdir), 'elf', 'c'),
                         Executable(Path('a'), 'elf', 'c'))


class TestSharedLibrary(FileTest):
    def test_clone(self):
        self.assertClone(SharedLibrary(Path('a', Root.srcdir), 'elf', 'c'),
                         SharedLibrary(Path('a'), 'elf', 'c'))


class TestVersionedSharedLibrary(FileTest):
    def test_clone(self):
        self.assertClone(
            VersionedSharedLibrary(
                Path('a.1.2.3', Root.srcdir), 'elf', 'c',
                Path('a.1', Root.srcdir), Path('a', Root.srcdir)
            ),
            VersionedSharedLibrary(
                Path('a.1.2.3'), 'elf', 'c', Path('a.1', Root.srcdir),
                Path('a', Root.srcdir)
            )
        )

    def test_clone_recursive(self):
        self.assertClone(
            VersionedSharedLibrary(
                Path('a.1.2.3', Root.srcdir), 'elf', 'c',
                Path('a.1', Root.srcdir), Path('a', Root.srcdir)
            ),
            VersionedSharedLibrary(
                Path('a.1.2.3'), 'elf', 'c', Path('a.1'), Path('a')
            ),
            recursive=True
        )

    def test_invalid_clone(self):
        lib = VersionedSharedLibrary(Path('a.1.2.3'), 'elf', 'c', Path('a.1'),
                                     Path('a'))
        with self.assertRaises(RuntimeError):
            lib.clone(pathfn, inner=File(Path('b')))


class TestLinkLibrary(FileTest):
    def test_clone(self):
        lib = VersionedSharedLibrary(
            Path('a.1.2.3', Root.srcdir), 'elf', 'c',
            Path('a.1', Root.srcdir), Path('a', Root.srcdir)
        )
        so_clone = LinkLibrary(Path('a.1'), lib)
        link_clone = LinkLibrary(Path('a'), lib.soname)

        self.assertClone(lib.soname, so_clone)
        self.assertClone(lib.link, link_clone)

    def test_clone_recursive(self):
        lib = VersionedSharedLibrary(
            Path('a.1.2.3', Root.srcdir), 'elf', 'c',
            Path('a.1', Root.srcdir), Path('a', Root.srcdir)
        )
        clone = VersionedSharedLibrary(
            Path('a.1.2.3'), 'elf', 'c', Path('a.1'), Path('a')
        )

        self.assertClone(lib.soname, clone.soname, recursive=True)
        self.assertClone(lib.link, clone.link, recursive=True)


class TestStaticLibrary(FileTest):
    def test_clone(self):
        self.assertClone(StaticLibrary(Path('a', Root.srcdir), 'elf', 'c'),
                         StaticLibrary(Path('a'), 'elf', 'c'))
        self.assertClone(StaticLibrary(Path('a', Root.srcdir), 'elf', 'c',
                                       {'foo': 'bar'}),
                         StaticLibrary(Path('a'), 'elf', 'c', {'foo': 'bar'}))


class TestExportFile(FileTest):
    def test_clone(self):
        self.assertClone(ExportFile(Path('a', Root.srcdir)),
                         ExportFile(Path('a')))


class TestDllBinary(FileTest):
    def test_clone(self):
        self.assertClone(
            DllBinary(Path('a.dll', Root.srcdir), 'elf', 'c',
                      Path('a.lib', Root.srcdir)),
            DllBinary(Path('a.dll'), 'elf', 'c', Path('a.lib', Root.srcdir))
        )
        self.assertClone(
            DllBinary(Path('a.dll', Root.srcdir), 'elf', 'c',
                      Path('a.lib', Root.srcdir), Path('a.exp', Root.srcdir)),
            DllBinary(Path('a.dll'), 'elf', 'c', Path('a.lib', Root.srcdir),
                      Path('a.exp', Root.srcdir))
        )

    def test_clone_recursive(self):
        self.assertClone(
            DllBinary(Path('a.dll', Root.srcdir), 'elf', 'c',
                      Path('a.lib', Root.srcdir)),
            DllBinary(Path('a.dll'), 'elf', 'c', Path('a.lib')),
            recursive=True
        )
        self.assertClone(
            DllBinary(Path('a.dll', Root.srcdir), 'elf', 'c',
                      Path('a.lib', Root.srcdir), Path('a.exp', Root.srcdir)),
            DllBinary(Path('a.dll'), 'elf', 'c', Path('a.lib'), Path('a.exp')),
            recursive=True
        )


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
        shared = SharedLibrary(Path('shared', Root.srcdir), 'elf', 'c')
        static = StaticLibrary(Path('static', Root.srcdir), 'elf', 'c')
        shared_install = SharedLibrary(Path('shared'), 'elf', 'c')
        static_install = StaticLibrary(Path('static'), 'elf', 'c')
        self.assertClone(DualUseLibrary(shared, static),
                         DualUseLibrary(shared_install, static_install))


class TestPkgConfigPcFile(FileTest):
    def test_clone(self):
        self.assertClone(PkgConfigPcFile(Path('a', Root.srcdir)),
                         PkgConfigPcFile(Path('a')))
