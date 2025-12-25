import os
import re
from contextlib import contextmanager
from unittest import mock

from .common import BuiltinTestCase
from .. import *

from bfg9000 import file_types
from bfg9000.builtins import builtin, packages, project  # noqa: F401
from bfg9000.iterutils import first
from bfg9000.path import abspath
from bfg9000.versioning import SpecifierSet, Version


def mock_which(names, *args, **kwargs):
    return [os.path.abspath('/' + first(first(names)))]


def mock_execute_common(args, **kwargs):
    prog = os.path.basename(args[0])
    if prog == 'mopack':
        if args[1] == 'linkage':
            pkg = args[5]
            if len(args) > 6 and args[6] == '-ssubmodule':
                pkg = pkg + '_submodule'
            return ('{"type": "pkg_config", "pcnames": ["' + pkg + '"], ' +
                    '"pkg_config_path": []}\n')
    elif prog == 'pkg-config':
        if '--modversion' in args:
            return '1.2.3\n'
        elif '--variable=mopack_generated' in args:
            return ''
        elif '--variable=pcfiledir' in args:
            return '/path/to/pkg-config'
        elif '--variable=bindir' in args:
            return '/path/to/bin'
        elif '--cflags-only-I' in args:
            return '/path/to/include'
    raise OSError('unknown command: {}'.format(args))


def mock_execute_cc(args, **kwargs):
    prog = os.path.basename(args[0])
    if prog in ('cc', 'c++'):
        if '--version' in args:
            return ('gcc (Ubuntu 5.4.0-6ubuntu1~16.04.9) 5.4.0 20160609\n' +
                    'Copyright (C) 2015 Free Software Foundation, Inc.\n')
        elif '-Wl,--version' in args:
            return '', '/usr/bin/ld --version\n'
        elif '-print-search-dirs' in args:
            return 'libraries: =/usr/lib\n'
        elif '-print-sysroot' in args:
            return '/\n'
    elif prog == 'ld':
        if '--verbose' in args:
            return 'SEARCH_DIR("/usr")\n'
    return mock_execute_common(args, **kwargs)


def mock_execute_msvc(args, **kwargs):
    prog = os.path.basename(args[0])
    if prog == 'cl':
        if '-?' in args:
            return ('Microsoft (R) C/C++ Optimizing Compiler Version ' +
                    '19.12.25831 for x86')
    return mock_execute_common(args, **kwargs)


class TestPackageCc(BuiltinTestCase):
    mock_execute = staticmethod(mock_execute_cc)
    mock_platform = 'linux'

    def setUp(self):
        self.env = make_env(self.mock_platform, clear_variables=True)
        self.build, self.context = self._make_context(self.env)
        self.bfgfile = file_types.File(self.build.bfgpath)

    def test_name(self):
        with mock.patch('bfg9000.shell.execute', self.mock_execute), \
             mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('logging.log'):
            pkg = self.context['package']('name')
            self.assertEqual(pkg.name, 'name')
            self.assertEqual(pkg.version, Version('1.2.3'))
            self.assertEqual(pkg.specifier, SpecifierSet())
            self.assertEqual(pkg.static, False)
            self.assertEqual(pkg.system, True)

    def test_submodules(self):
        with mock.patch('bfg9000.shell.execute', self.mock_execute), \
             mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('logging.log'):
            pkg = self.context['package']('name', 'submodule')
            self.assertEqual(pkg.name, 'name[submodule]')
            self.assertEqual(pkg.version, Version('1.2.3'))
            self.assertEqual(pkg.specifier, SpecifierSet())
            self.assertEqual(pkg.static, False)
            self.assertEqual(pkg.system, True)

    def test_version(self):
        with mock.patch('bfg9000.shell.execute', self.mock_execute), \
             mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('logging.log'):
            pkg = self.context['package']('name', '>1.0')
            self.assertEqual(pkg.name, 'name')
            self.assertEqual(pkg.version, Version('1.2.3'))
            self.assertEqual(pkg.specifier, SpecifierSet('>1.0'))
            self.assertEqual(pkg.static, False)
            self.assertEqual(pkg.system, True)

    def test_submodules_and_version(self):
        with mock.patch('bfg9000.shell.execute', self.mock_execute), \
             mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('logging.log'):
            pkg = self.context['package']('name', 'submodule', '>1.0')
            self.assertEqual(pkg.name, 'name[submodule]')
            self.assertEqual(pkg.version, Version('1.2.3'))
            self.assertEqual(pkg.specifier, SpecifierSet('>1.0'))
            self.assertEqual(pkg.static, False)
            self.assertEqual(pkg.system, True)

    def test_lang(self):
        with mock.patch('bfg9000.shell.execute', self.mock_execute), \
             mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('logging.log'):
            pkg = self.context['package']('name', lang='c++')
            self.assertEqual(pkg.name, 'name')
            self.assertEqual(pkg.version, Version('1.2.3'))
            self.assertEqual(pkg.specifier, SpecifierSet())
            self.assertEqual(pkg.static, False)
            self.assertEqual(pkg.system, True)

    def test_kind(self):
        with mock.patch('bfg9000.shell.execute', self.mock_execute), \
             mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('logging.log'):
            pkg = self.context['package']('name', kind='static')
            self.assertEqual(pkg.name, 'name')
            self.assertEqual(pkg.version, Version('1.2.3'))
            self.assertEqual(pkg.specifier, SpecifierSet())
            self.assertEqual(pkg.static, True)
            self.assertEqual(pkg.system, True)

    def test_system(self):
        with mock.patch('bfg9000.shell.execute', self.mock_execute), \
             mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('logging.log'):
            pkg = self.context['package']('name', system=False)
            self.assertEqual(pkg.name, 'name')
            self.assertEqual(pkg.version, Version('1.2.3'))
            self.assertEqual(pkg.specifier, SpecifierSet())
            self.assertEqual(pkg.static, False)
            self.assertEqual(pkg.system, False)

    def test_guess_lang(self):
        @contextmanager
        def mock_context():
            mock_obj = mock.patch.object
            with mock_obj(self.env, 'builder', wraps=self.env.builder) as m, \
                 mock.patch('bfg9000.shell.execute', self.mock_execute), \
                 mock.patch('bfg9000.shell.which', mock_which), \
                 mock.patch('logging.log'):
                yield m

        package = self.context['package']

        with mock_context() as m:
            pkg = package('name')
            self.assertEqual(pkg.name, 'name')
            m.assert_called_with('c')

        self.context['project'](lang='c++')
        with mock_context() as m:
            pkg = package('name')
            self.assertEqual(pkg.name, 'name')
            m.assert_called_with('c++')

    def test_boost_package(self):
        def mock_exists(x):
            x = x.string()
            return bool(re.search(r'[/\\]boost[/\\]version.hpp$', x) or
                        re.search(r'[/\\]libboost_thread', x) or
                        x in ['/usr/include', '/usr/lib'])

        with mock.patch('bfg9000.shell.execute', self.mock_execute), \
             mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('logging.log'):
            pkg = self.context['package']('boost', 'thread')
            self.assertEqual(pkg.name, 'boost[thread]')
            self.assertEqual(pkg.version, Version('1.2.3'))

    def test_invalid_kind(self):
        with self.assertRaises(ValueError):
            self.context['package']('name', kind='bad')


class TestPackageMsvc(TestPackageCc):
    mock_execute = staticmethod(mock_execute_msvc)
    mock_platform = 'winnt'


class TestSystemExecutable(BuiltinTestCase):
    def test_name(self):
        with mock.patch('bfg9000.builtins.packages.which', mock_which):
            self.assertEqual(
                self.context['system_executable']('name'),
                file_types.Executable(abspath('/name'),
                                      self.env.target_platform.object_format)
            )

    def test_package(self):
        env = make_env('linux', clear_variables=True)
        build, context = self._make_context(env)

        with mock.patch('bfg9000.shell.execute', mock_execute_cc), \
             mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('os.path.exists', return_value=True), \
             mock.patch('logging.log'):
            pkg = context['package']('name')
            prog = context['system_executable']('program', package=pkg)
            self.assertEqual(prog.path, abspath('/path/to/bin/program',
                                                absdrive=False))

    def test_format(self):
        with mock.patch('bfg9000.builtins.packages.which', mock_which):
            self.assertEqual(
                self.context['system_executable']('name', 'format'),
                file_types.Executable(abspath('/name'), 'format')
            )
