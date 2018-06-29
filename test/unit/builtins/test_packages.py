import mock
import os
import re
import unittest
from collections import namedtuple

from bfg9000 import file_types, options as opts
from bfg9000.builtins import packages
from bfg9000.environment import Environment
from bfg9000.exceptions import PackageResolutionError
from bfg9000.file_types import CommonPackage, Directory, HeaderDirectory
from bfg9000.path import abspath
from bfg9000.platforms import platform_name, platform_info
from bfg9000.versioning import SpecifierSet, Version


def mock_which(*args, **kwargs):
    return [os.path.abspath('/command')]


def mock_execute(args, **kwargs):
    if args[-1] == '--version':
        return ('gcc (Ubuntu 5.4.0-6ubuntu1~16.04.9) 5.4.0 20160609\n' +
                'Copyright (C) 2015 Free Software Foundation, Inc.\n')
    elif args[-1] == '-Wl,--version':
        return '', '/usr/bin/ld --version\n'
    elif args[-1] == '-print-search-dirs':
        return 'libraries: =/usr/lib\n'
    elif args[-1] == '-print-sysroot':
        return '/\n'
    elif args[-1] == '--verbose':
        return 'SEARCH_DIR("/usr")\n'
    elif args[-1] == '/?':
        return ('Microsoft (R) C/C++ Optimizing Compiler Version ' +
                '19.12.25831 for x86')
    elif args[-1] == '--modversion':
        return '1.2.3\n'


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.env = Environment(None, None, None, None, None, {},
                               (False, False), None)


class TestFramework(BaseTest):
    @unittest.skipIf(platform_name() != 'darwin',
                     'frameworks only exist on macOS')
    def test_framework(self):
        self.assertEqual(
            packages.framework(self.env, 'name'),
            CommonPackage('name', self.env.platform.object_format,
                          link_options=opts.option_list(opts.lib(
                              file_types.Framework('name')
                          )))
        )

    @unittest.skipIf(platform_name() != 'darwin',
                     'frameworks only exist on macOS')
    def test_framework_suffix(self):
        self.assertEqual(
            packages.framework(self.env, 'name', 'suffix'),
            CommonPackage('name,suffix', self.env.platform.object_format,
                          link_options=opts.option_list(opts.lib(
                              file_types.Framework('name', 'suffix')
                          )))
        )

    @unittest.skipIf(platform_name() == 'darwin',
                     'frameworks only exist on macOS')
    def test_frameworks_unsupported(self):
        with self.assertRaises(PackageResolutionError):
            packages.framework(self.env, 'name')

        with self.assertRaises(PackageResolutionError):
            packages.framework(self.env, 'name', 'suffix')


class TestPackage(BaseTest):
    def test_name(self):
        with mock.patch('bfg9000.shell.execute', mock_execute), \
             mock.patch('bfg9000.shell.which', mock_which):  # noqa
            pkg = packages.package(self.env, 'name')
            self.assertEqual(pkg.name, 'name')
            self.assertEqual(pkg.version, Version('1.2.3'))
            self.assertEqual(pkg.specifier, SpecifierSet())
            self.assertEqual(pkg.static, False)

    def test_version(self):
        with mock.patch('bfg9000.shell.execute', mock_execute), \
             mock.patch('bfg9000.shell.which', mock_which):  # noqa
            pkg = packages.package(self.env, 'name', version='>1.0')
            self.assertEqual(pkg.name, 'name')
            self.assertEqual(pkg.version, Version('1.2.3'))
            self.assertEqual(pkg.specifier, SpecifierSet('>1.0'))
            self.assertEqual(pkg.static, False)

    def test_lang(self):
        with mock.patch('bfg9000.shell.execute', mock_execute), \
             mock.patch('bfg9000.shell.which', mock_which):  # noqa
            pkg = packages.package(self.env, 'name', lang='c++')
            self.assertEqual(pkg.name, 'name')
            self.assertEqual(pkg.version, Version('1.2.3'))
            self.assertEqual(pkg.specifier, SpecifierSet())
            self.assertEqual(pkg.static, False)

    def test_kind(self):
        with mock.patch('bfg9000.shell.execute', mock_execute), \
             mock.patch('bfg9000.shell.which', mock_which):  # noqa
            pkg = packages.package(self.env, 'name', kind='static')
            self.assertEqual(pkg.name, 'name')
            self.assertEqual(pkg.version, Version('1.2.3'))
            self.assertEqual(pkg.specifier, SpecifierSet())
            self.assertEqual(pkg.static, True)

    def test_invalid_kind(self):
        with self.assertRaises(ValueError):
            packages.package(self.env, 'name', kind='bad')


class TestBoostPackage(BaseTest):
    @unittest.skipIf(platform_name() != 'windows',
                     'special default location only applies to windows')
    def test_windows_default_location(self):
        exists = os.path.exists
        boost_dir = os.path.abspath('boost-1.23')

        def mock_find(*args, **kwargs):
            return [boost_dir]

        def mock_boost_version(*args, **kwargs):
            return Version('1.23')

        def mock_exists(x):
            if re.search(r'[/\\]boost[/\\]version.hpp$', x):
                return True
            return exists(x)

        # Clear the environment variables to force this to use the default
        # location.
        self.env.variables = {}

        with mock.patch('bfg9000.builtins.packages.find', mock_find), \
             mock.patch('bfg9000.builtins.packages._boost_version',
                        mock_boost_version), \
             mock.patch('os.path.exists', mock_exists):  # noqa
            pkg = packages.boost_package(self.env, 'thread')
            self.assertEqual(pkg.name, 'boost(thread)')
            self.assertEqual(pkg._compile_options, opts.option_list(
                opts.include_dir(HeaderDirectory(abspath(boost_dir)))
            ))
            self.assertEqual(pkg._link_options, opts.option_list(
                opts.lib_dir(Directory(abspath(r'C:\Boost\lib')))
            ))


class TestSystemExecutable(BaseTest):
    def test_name(self):
        with mock.patch('bfg9000.builtins.packages.which', mock_which):
            self.assertEqual(
                packages.system_executable(self.env, 'name'),
                file_types.Executable(abspath('/command'),
                                      self.env.platform.object_format)
            )

    def test_format(self):
        with mock.patch('bfg9000.builtins.packages.which', mock_which):
            self.assertEqual(
                packages.system_executable(self.env, 'name', 'format'),
                file_types.Executable(abspath('/command'), 'format')
            )
