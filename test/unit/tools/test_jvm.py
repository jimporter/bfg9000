import mock
import os

from .. import *

from bfg9000 import file_types, options as opts
from bfg9000.languages import Languages
from bfg9000.safe_str import jbos
from bfg9000.tools.jvm import JvmBuilder
from bfg9000.versioning import Version

known_langs = Languages()
with known_langs.make('java') as x:
    x.vars(compiler='JAVAC', runner='JAVACMD', flags='JAVAFLAGS')
with known_langs.make('scala') as x:
    x.vars(compiler='SCALAC', runner='SCALACMD', flags='SCALAFLAGS')


def mock_which(*args, **kwargs):
    return ['command']


class TestJvmBuilder(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        CrossPlatformTestCase.__init__(self, clear_variables=True, *args,
                                       **kwargs)

    def test_properties(self):
        def mock_execute(*args, **kwargs):
            return 'version'

        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            jvm = JvmBuilder(self.env, known_langs['java'], ['javac'],
                             'version')

        self.assertEqual(jvm.flavor, 'jvm')
        self.assertEqual(jvm.compiler.flavor, 'jvm')
        self.assertEqual(jvm.linker('executable').flavor, 'jar')
        self.assertEqual(jvm.linker('shared_library').flavor, 'jar')

        self.assertEqual(jvm.family, 'jvm')
        self.assertEqual(jvm.can_dual_link, False)

        self.assertEqual(jvm.compiler.deps_flavor, None)
        self.assertEqual(jvm.compiler.needs_libs, True)
        self.assertEqual(jvm.compiler.accepts_pch, False)

        self.assertRaises(AttributeError, lambda: jvm.pch_compiler)
        self.assertRaises(KeyError, lambda: jvm.linker('unknown'))
        self.assertRaises(ValueError, lambda: jvm.linker('static_library'))

    def test_oracle(self):
        def mock_execute(*args, **kwargs):
            return ('java version "1.7.0_55"\n' +
                    'Java(TM) SE Runtime Environment (build 1.7.0_55-b13)')

        version = 'javac 1.7.0_55'
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            jvm = JvmBuilder(self.env, known_langs['java'], ['javac'], version)

        self.assertEqual(jvm.brand, 'oracle')
        self.assertEqual(jvm.compiler.brand, 'oracle')
        self.assertEqual(jvm.linker('executable').brand, 'oracle')
        self.assertEqual(jvm.linker('shared_library').brand, 'oracle')

        self.assertEqual(jvm.version, Version('1.7.0'))
        self.assertEqual(jvm.compiler.version, Version('1.7.0'))
        self.assertEqual(jvm.linker('executable').version, Version('1.7.0'))
        self.assertEqual(jvm.linker('shared_library').version,
                         Version('1.7.0'))

    def test_openjdk(self):
        def mock_execute(*args, **kwargs):
            return ('openjdk version "1.8.0_151"\n' +
                    'OpenJDK Runtime Environment (build ' +
                    '1.8.0_151-8u151-b12-0ubuntu0.16.04.2-b12)')

        version = 'javac 1.8.0_151'
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            jvm = JvmBuilder(self.env, known_langs['java'], ['javac'], version)

        self.assertEqual(jvm.brand, 'openjdk')
        self.assertEqual(jvm.compiler.brand, 'openjdk')
        self.assertEqual(jvm.linker('executable').brand, 'openjdk')
        self.assertEqual(jvm.linker('shared_library').brand, 'openjdk')

        self.assertEqual(jvm.version, Version('1.8.0'))
        self.assertEqual(jvm.compiler.version, Version('1.8.0'))
        self.assertEqual(jvm.linker('executable').version, Version('1.8.0'))
        self.assertEqual(jvm.linker('shared_library').version,
                         Version('1.8.0'))

    def test_scala(self):
        version = ('Scala code runner version 2.11.6 -- ' +
                   'Copyright 2002-2013, LAMP/EPFL')
        with mock.patch('bfg9000.shell.which', mock_which):  # noqa
            jvm = JvmBuilder(self.env, known_langs['scala'], ['scalac'],
                             version)

        self.assertEqual(jvm.brand, 'epfl')
        self.assertEqual(jvm.compiler.brand, 'epfl')
        self.assertEqual(jvm.linker('executable').brand, 'epfl')
        self.assertEqual(jvm.linker('shared_library').brand, 'epfl')

        self.assertEqual(jvm.version, Version('2.11.6'))
        self.assertEqual(jvm.compiler.version, Version('2.11.6'))
        self.assertEqual(jvm.linker('executable').version, Version('2.11.6'))
        self.assertEqual(jvm.linker('shared_library').version,
                         Version('2.11.6'))

    def test_unknown_brand(self):
        def mock_execute(*args, **kwargs):
            return 'unknown'

        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            jvm = JvmBuilder(self.env, known_langs['java'], ['javac'],
                             'unknown')

        self.assertEqual(jvm.brand, 'unknown')
        self.assertEqual(jvm.compiler.brand, 'unknown')
        self.assertEqual(jvm.linker('executable').brand, 'unknown')
        self.assertEqual(jvm.linker('shared_library').brand, 'unknown')

        self.assertEqual(jvm.version, None)
        self.assertEqual(jvm.compiler.version, None)
        self.assertEqual(jvm.linker('executable').version, None)
        self.assertEqual(jvm.linker('shared_library').version, None)

    def test_broken_brand(self):
        def mock_execute(*args, **kwargs):
            raise OSError()

        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            jvm = JvmBuilder(self.env, known_langs['java'], ['javac'],
                             'version')

        self.assertEqual(jvm.brand, 'unknown')
        self.assertEqual(jvm.compiler.brand, 'unknown')
        self.assertEqual(jvm.linker('executable').brand, 'unknown')
        self.assertEqual(jvm.linker('shared_library').brand, 'unknown')

        self.assertEqual(jvm.version, None)
        self.assertEqual(jvm.compiler.version, None)
        self.assertEqual(jvm.linker('executable').version, None)
        self.assertEqual(jvm.linker('shared_library').version, None)


class TestJvmCompiler(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        CrossPlatformTestCase.__init__(self, clear_variables=True, *args,
                                       **kwargs)

    def setUp(self):
        def mock_execute(*args, **kwargs):
            return 'version'

        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            self.compiler = JvmBuilder(self.env, known_langs['java'],
                                       ['javac'], 'version').compiler

    def test_flags_empty(self):
        self.assertEqual(self.compiler.flags(opts.option_list()), [])

    def test_flags_lib(self):
        lib1 = self.Path('/path/to/lib/libfoo.jar')
        lib2 = self.Path('/path/to/lib/libbar.jar')

        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.lib(file_types.StaticLibrary(lib1, 'jvm'))
        )), ['-cp', jbos(lib1)])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.lib(file_types.StaticLibrary(lib1, 'jvm')),
            opts.lib(file_types.StaticLibrary(lib2, 'jvm'))
        )), ['-cp', lib1 + os.pathsep + lib2])

    def test_flags_debug(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.debug()
        )), ['-g'])

        version = ('Scala code runner version 2.11.6 -- ' +
                   'Copyright 2002-2013, LAMP/EPFL')
        with mock.patch('bfg9000.shell.which', mock_which):  # noqa
            scala_compiler = JvmBuilder(self.env, known_langs['scala'],
                                        ['scalac'], version).compiler
        self.assertEqual(scala_compiler.flags(opts.option_list(
            opts.debug()
        )), ['-g:vars'])

    def test_flags_warning(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('disable')
        )), ['-nowarn'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('all')
        )), ['-Xlint:all'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('error')
        )), ['-Werror'])
        with self.assertRaises(ValueError):
            self.compiler.flags(opts.option_list(opts.warning('extra')))

        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('all', 'error')
        )), ['-Xlint:all', '-Werror'])

    def test_flags_warning_scala(self):
        version = ('Scala code runner version 2.11.6 -- ' +
                   'Copyright 2002-2013, LAMP/EPFL')
        with mock.patch('bfg9000.shell.which', mock_which):  # noqa
            self.compiler = JvmBuilder(self.env, known_langs['scala'],
                                       ['scalac'], version).compiler

        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('disable')
        )), ['-nowarn'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('all')
        )), ['-Xlint:_'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('error')
        )), ['-Xfatal-errors'])
        with self.assertRaises(ValueError):
            self.compiler.flags(opts.option_list(opts.warning('extra')))

        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('all', 'error')
        )), ['-Xlint:_', '-Xfatal-errors'])

        with self.assertRaises(ValueError):
            self.compiler.flags(opts.option_list(opts.warning('unknown')))

    def test_flags_optimize(self):
        version = ('Scala code runner version 2.11.6 -- ' +
                   'Copyright 2002-2013, LAMP/EPFL')
        with mock.patch('bfg9000.shell.which', mock_which):  # noqa
            self.compiler = JvmBuilder(self.env, known_langs['scala'],
                                       ['scalac'], version).compiler

        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.optimize('disable')
        )), [])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.optimize('size')
        )), ['-optimize'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.optimize('speed')
        )), ['-optimize'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.optimize('linktime')
        )), [])

        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.optimize('speed', 'linktime')
        )), ['-optimize'])

    def test_flags_string(self):
        self.assertEqual(self.compiler.flags(opts.option_list('-v')), ['-v'])

    def test_flags_invalid(self):
        with self.assertRaises(TypeError):
            self.compiler.flags(opts.option_list(123))


class TestJvmLinker(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        CrossPlatformTestCase.__init__(self, clear_variables=True, *args,
                                       **kwargs)

    def setUp(self):
        def mock_execute(*args, **kwargs):
            return 'version'

        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            self.linker = JvmBuilder(self.env, known_langs['java'], ['javac'],
                                     'version').linker('executable')

    def test_flags_empty(self):
        self.assertEqual(self.linker.flags(opts.option_list()), [])

    def test_flags_string(self):
        self.assertEqual(self.linker.flags(opts.option_list('-v')), ['-v'])

    def test_flags_debug(self):
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.debug()
        )), [])

    def test_flags_optimize(self):
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.optimize('size')
        )), [])

    def test_flags_invalid(self):
        with self.assertRaises(TypeError):
            self.linker.flags(opts.option_list(123))
