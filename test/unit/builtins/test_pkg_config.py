import os
from io import StringIO
from unittest import mock

from .common import BuiltinTest, TestCase

from bfg9000.builtins import (default, link, packages, project,  # noqa: F401
                              version)
from bfg9000.builtins.pkg_config import *
from bfg9000.safe_str import safe_str, shell_literal
from bfg9000.shell import CalledProcessError
from bfg9000.versioning import SpecifierSet


def mock_execute(args, **kwargs):
    name = args[1]
    if name.endswith('-uninstalled'):
        raise CalledProcessError(1, args)

    if '--modversion' in args:
        return '1.0\n'
    elif '--print-requires' in args:
        return '\n'
    elif '--variable=install_names' in args:
        return '/usr/lib/lib{}.dylib'.format(name)
    elif '--cflags-only-I' in args:
        return '-I/usr/include/{}\n'.format(name)
    elif '--cflags-only-other' in args:
        return '-D{}\n'.format(name.upper())
    elif '--libs-only-L' in args:
        return '-L/usr/lib/{}\n'.format(name)
    elif '--libs-only-other' in args:
        return '-pthread\n'
    elif '--libs-only-l' in args:
        if '--static' in args:
            return '-l{}\n -lstatic'.format(name)
        return '-l{}\n'.format(name)
    raise OSError('unknown command: {}'.format(args))


class TestPkgConfigRequirement(TestCase):
    def test_merge_requirements(self):
        a = Requirement('foo', '>=1.0')
        b = Requirement('foo', '<=2.0')
        c = Requirement('bar', '<=2.0')

        self.assertEqual(a & b, Requirement('foo', '>=1.0,<=2.0'))
        a &= b
        self.assertEqual(a, Requirement('foo', '>=1.0,<=2.0'))
        self.assertRaises(ValueError, lambda: b & c)

    def test_split_requirement(self):
        a = Requirement('foo')
        self.assertEqual(set(a.split()), {SimpleRequirement('foo')})
        a = Requirement('foo', '>=1.0')
        self.assertEqual(set(a.split()), {SimpleRequirement('foo', '>=1.0')})
        a = Requirement('foo', '>=1.0,<=2.0')
        self.assertEqual(set(a.split()), {SimpleRequirement('foo', '>=1.0'),
                                          SimpleRequirement('foo', '<=2.0')})

    def test_split_requirement_single(self):
        a = Requirement('foo')
        self.assertEqual(set(a.split(True)), {SimpleRequirement('foo')})
        a = Requirement('foo', '>=1.0')
        self.assertEqual(set(a.split(True)),
                         {SimpleRequirement('foo', '>=1.0')})
        a = Requirement('foo', '>=1.0,<=2.0')
        self.assertRaises(ValueError, lambda: a.split(True))

    def test_equality(self):
        R, S = Requirement, SimpleRequirement
        self.assertTrue(R('foo', '>=1.0') == R('foo', '>=1.0'))
        self.assertFalse(R('foo', '>=1.0') != R('foo', '>=1.0'))

        self.assertTrue(S('foo', '>=1.0') == S('foo', '>=1.0'))
        self.assertFalse(S('foo', '>=1.0') != S('foo', '>=1.0'))

        self.assertFalse(R('foo', '>=1.0') == R('bar', '>=1.0'))
        self.assertTrue(R('foo', '>=1.0') != R('bar', '>=1.0'))
        self.assertFalse(R('foo', '>=1.0') == R('foo', '>=2.0'))
        self.assertTrue(R('foo', '>=1.0') != R('foo', '>=2.0'))

        self.assertFalse(S('foo', '>=1.0') == S('bar', '>=1.0'))
        self.assertTrue(S('foo', '>=1.0') != S('bar', '>=1.0'))
        self.assertFalse(S('foo', '>=1.0') == S('foo', '>=2.0'))
        self.assertTrue(S('foo', '>=1.0') != S('foo', '>=2.0'))

        self.assertFalse(R('foo', '>=1.0') == S('foo', '>=1.0'))
        self.assertTrue(R('foo', '>=1.0') != S('foo', '>=1.0'))
        self.assertFalse(S('foo', '>=1.0') == R('foo', '>=1.0'))
        self.assertTrue(S('foo', '>=1.0') != R('foo', '>=1.0'))


class TestPkgConfigSimpleRequirement(TestCase):
    def test_stringify(self):
        r = SimpleRequirement('foo', '>=1.0')
        self.assertEqual(safe_str(r), shell_literal('foo >= 1.0'))

    def test_stringify_equal(self):
        r = SimpleRequirement('foo', '==1.0')
        self.assertEqual(safe_str(r), shell_literal('foo = 1.0'))

    def test_stringify_no_version(self):
        r = SimpleRequirement('foo')
        self.assertEqual(safe_str(r), shell_literal('foo'))


class TestPkgConfigRequirementSet(TestCase):
    def test_init(self):
        s = RequirementSet([Requirement('foo', '>=1.0'),
                            Requirement('foo', '<=2.0'),
                            Requirement('bar', '>=3.0')])
        self.assertEqual(set(s), {Requirement('foo', '>=1.0,<=2.0'),
                                  Requirement('bar', '>=3.0')})

    def test_add(self):
        s = RequirementSet()
        s.add(Requirement('foo', '>=1.0'))
        s.add(Requirement('foo', '<=2.0'))
        s.add(Requirement('bar', '>=3.0'))
        self.assertEqual(set(s), {Requirement('foo', '>=1.0,<=2.0'),
                                  Requirement('bar', '>=3.0')})

    def test_remove(self):
        s = RequirementSet([Requirement('foo', '>=1.0'),
                            Requirement('foo', '<=2.0'),
                            Requirement('bar', '>=3.0')])
        s.remove('foo')
        self.assertEqual(set(s), {Requirement('bar', '>=3.0')})

    def test_update(self):
        a = RequirementSet([Requirement('foo', '>=1.0'),
                            Requirement('bar', '>=3.0')])
        b = RequirementSet([Requirement('foo', '<=2.0'),
                            Requirement('baz', '>=4.0')])
        a.update(b)
        self.assertEqual(set(a), {Requirement('foo', '>=1.0,<=2.0'),
                                  Requirement('bar', '>=3.0'),
                                  Requirement('baz', '>=4.0')})

    def test_merge_from(self):
        a = RequirementSet([Requirement('foo', '>=1.0'),
                            Requirement('bar', '>=3.0')])
        b = RequirementSet([Requirement('foo', '<=2.0'),
                            Requirement('baz', '>=4.0')])
        a.merge_from(b)
        self.assertEqual(set(a), {Requirement('foo', '>=1.0,<=2.0'),
                                  Requirement('bar', '>=3.0')})
        self.assertEqual(set(b), {Requirement('baz', '>=4.0')})

    def test_split(self):
        s = RequirementSet([Requirement('foo', '>=1.0'),
                            Requirement('foo', '<=2.0'),
                            Requirement('bar', '>=3.0')])
        self.assertEqual(set(s.split()), {SimpleRequirement('bar', '>=3.0'),
                                          SimpleRequirement('foo', '>=1.0'),
                                          SimpleRequirement('foo', '<=2.0')})


class TestSimpleProperty(TestCase):
    class Foo:
        @PkgConfigInfo._simple_property
        def my_prop(self, value):
            return value.upper()

    def test_owner(self):
        self.assertIsInstance(self.Foo.my_prop, PkgConfigInfo._simple_property)

    def test_get_set(self):
        f = self.Foo()
        f.my_prop = 'value'
        self.assertEqual(f.my_prop, 'VALUE')
        f.my_prop = None
        self.assertEqual(f.my_prop, None)


class TestPkgConfig(BuiltinTest):
    def setUp(self):
        super().setUp()

    def get_pkg_config(self):
        def mock_execute_cc(args, **kwargs):
            if '--version' in args:
                return 'version\n'
            raise OSError('unknown command: {}'.format(args))

        with mock.patch('bfg9000.shell.which', return_value=['command']), \
             mock.patch('bfg9000.shell.execute', mock_execute_cc):
            self.context.env.builder('c')
        return self.context.env.tool('pkg_config')

    def test_minimal(self):
        pkg = PkgConfigInfo(self.context, name='package')
        data = pkg.finalize()

        out = StringIO()
        PkgConfigWriter(self.context)._write(out, data, installed=True)
        self.assertRegex(out.getvalue(),
                         '\n\nName: package\n' +
                         'Description: package library\n' +
                         'Version: 0.0\n$')

    def test_metadata(self):
        pkg = PkgConfigInfo(
            self.context, name='package', desc_name='my-package',
            desc='a cool package', url='http://www.example.com/', version='1.0'
        )
        data = pkg.finalize()

        out = StringIO()
        PkgConfigWriter(self.context)._write(out, data, installed=True)
        self.assertRegex(out.getvalue(),
                         '\n\nName: my-package\n' +
                         'Description: a cool package\n' +
                         'URL: http://www.example.com/\n' +
                         'Version: 1.0\n$')

    def test_metadata_uninstalled(self):
        pkg = PkgConfigInfo(
            self.context, name='package', desc_name='my-package',
            desc='a cool package', url='http://www.example.com/', version='1.0'
        )
        data = pkg.finalize()

        out = StringIO()
        PkgConfigWriter(self.context)._write(out, data, installed=False)
        self.assertRegex(out.getvalue(),
                         '\n\nName: my-package \\(uninstalled\\)\n' +
                         'Description: a cool package\n' +
                         'URL: http://www.example.com/\n' +
                         'Version: 1.0\n$')

    def test_requires(self):
        pkg = PkgConfigInfo(
            self.context, name='package', version='1.0',
            requires=['req', ('vreq', '>=1.0'),
                      ('vreq2', SpecifierSet('>=1.1'))],
            requires_private=['preq'],
            conflicts=['creq']
        )
        data = pkg.finalize()

        out = StringIO()
        PkgConfigWriter(self.context)._write(out, data, installed=True)
        self.assertIn('\nRequires: req, vreq >= 1.0, vreq2 >= 1.1\n',
                      out.getvalue())
        self.assertIn('\nRequires.private: preq\n', out.getvalue())
        self.assertIn('\nConflicts: creq\n', out.getvalue())

        with self.assertRaises(TypeError):
            pkg = PkgConfigInfo(self.context, requires=[1])
        with self.assertRaises(TypeError):
            pkg = PkgConfigInfo(self.context, requires=[
                Package('foo', format='elf'),
            ])

    def test_requires_common_package(self):
        req = CommonPackage(pkg_config, 'req', format='elf',
                            compile_options=['-Ireq'],
                            link_options=['-lreq'])
        preq = CommonPackage(pkg_config, 'preq', format='elf',
                             compile_options=['-Ipreq'],
                             link_options=['-lpreq'])
        creq = CommonPackage(pkg_config, 'creq', format='elf',
                             compile_options=['-Icreq'],
                             link_options=['-lcreq'])

        pkg = PkgConfigInfo(
            self.context, name='package', version='1.0',
            requires=[req],
            requires_private=[preq],
            conflicts=[creq]
        )
        data = pkg.finalize()

        out = StringIO()
        PkgConfigWriter(self.context)._write(out, data, installed=True)
        self.assertIn('\nCflags: -Ireq -Ipreq\n', out.getvalue())
        self.assertIn('\nLibs: -lreq\n', out.getvalue())
        self.assertIn('\nLibs.private: -lpreq\n', out.getvalue())
        self.assertNotIn('\nRequires:', out.getvalue())
        self.assertNotIn('\nRequires.private:', out.getvalue())
        self.assertNotIn('\nConflicts:', out.getvalue())

    def test_requires_pkg_config_package(self):
        pkg_config = self.get_pkg_config()
        with mock.patch('bfg9000.shell.execute', mock_execute):
            req = PkgConfigPackage(pkg_config, 'req', format='elf')
            vreq = PkgConfigPackage(pkg_config, 'vreq', format='elf',
                                    specifier=SpecifierSet('>=1.0'))
            preq = PkgConfigPackage(pkg_config, 'preq', format='elf')
            creq = PkgConfigPackage(pkg_config, 'creq', format='elf')

        pkg = PkgConfigInfo(
            self.context, name='package', version='1.0',
            requires=[req, vreq],
            requires_private=[preq],
            conflicts=[creq]
        )
        data = pkg.finalize()

        out = StringIO()
        PkgConfigWriter(self.context)._write(out, data, installed=True)
        self.assertIn('\nRequires: req, vreq >= 1.0\n', out.getvalue())
        self.assertIn('\nRequires.private: preq\n', out.getvalue())
        self.assertIn('\nConflicts: creq\n', out.getvalue())

    def test_requires_generated_pkg_config_package(self):
        def pathstr(p):
            p = os.path.normpath(p)
            return "'{}'".format(p) if '\\' in p else p

        pkg_config = self.get_pkg_config()
        with mock.patch('bfg9000.shell.execute', mock_execute):
            req = GeneratedPkgConfigPackage(pkg_config, 'req', format='elf')
            preq = GeneratedPkgConfigPackage(pkg_config, 'preq', format='elf')
            creq = GeneratedPkgConfigPackage(pkg_config, 'creq', format='elf')

            pkg = PkgConfigInfo(
                self.context, name='package', version='1.0',
                requires=[req],
                requires_private=[preq],
                conflicts=[creq]
            )
            data = pkg.finalize()

            out = StringIO()
            PkgConfigWriter(self.context)._write(out, data, installed=True)

        self.assertIn('\nCflags: -DREQ -I{} -DPREQ -I{}\n'
                      .format(pathstr('/usr/include/req'),
                              pathstr('/usr/include/preq')),
                      out.getvalue())
        self.assertIn('\nLibs: -pthread -L{} -lreq\n'
                      .format(pathstr('/usr/lib/req')),
                      out.getvalue())
        self.assertIn('\nLibs.private: -pthread -L{} -lpreq\n'
                      .format(pathstr('/usr/lib/preq')),
                      out.getvalue())
        self.assertNotIn('\nRequires:', out.getvalue())
        self.assertNotIn('\nRequires.private:', out.getvalue())
        self.assertNotIn('\nConflicts:', out.getvalue())

    def test_includes_libs(self):
        public = self.context['shared_library']('public', 'public.cpp')

        static_library = self.context['static_library']
        inner = static_library('inner', 'inner.cpp', link_options=['-inner'])
        middle = static_library('middle', 'middle.cpp', libs=inner,
                                link_options=['-middle'])
        private = static_library('private', 'private.cpp', libs=middle)

        pkg = PkgConfigInfo(
            self.context, name='package', version='1.0',
            includes=['include'], libs=[public], libs_private=[private]
        )
        data = pkg.finalize()

        out = StringIO()
        PkgConfigWriter(self.context)._write(out, data, installed=True)
        self.assertIn("\nCflags: -I'${includedir}'\n", out.getvalue())
        # We intentionally don't check the newline at the end, since MinGW
        # generates `-lpublic.dll`.
        self.assertIn("\nLibs: -L'${libdir}' -lpublic", out.getvalue())
        self.assertIn("\nLibs.private: -middle -inner -L'${libdir}' " +
                      '-lprivate -lmiddle -linner\n', out.getvalue())

    def test_no_name(self):
        pkg = PkgConfigInfo(self.context)
        self.assertRaises(ValueError, pkg.finalize)
