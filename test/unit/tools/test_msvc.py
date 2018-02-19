import mock
import unittest

from bfg9000.environment import Environment
from bfg9000.tools.msvc import MsvcBuilder
from bfg9000.versioning import Version

env = Environment(None, None, None, None, None, {}, (False, False), None)


class TestMsvcBuilder(unittest.TestCase):
    def test_properties(self):
        with mock.patch('bfg9000.shell.which',
                        lambda *args, **kwargs: ['command']):
            cc = MsvcBuilder(env, 'c++', 'CXX', ['cl'], 'CXXFLAGS', [],
                             'version')

        self.assertEqual(cc.flavor, 'msvc')
        self.assertEqual(cc.compiler.flavor, 'msvc')
        self.assertEqual(cc.pch_compiler.flavor, 'msvc')
        self.assertEqual(cc.linker('executable').flavor, 'msvc')
        self.assertEqual(cc.linker('shared_library').flavor, 'msvc')
        self.assertEqual(cc.linker('static_library').flavor, 'msvc')

        self.assertEqual(cc.family, 'native')
        self.assertEqual(cc.auto_link, True)
        self.assertEqual(cc.can_dual_link, False)

        self.assertEqual(cc.compiler.num_outputs, 1)
        self.assertEqual(cc.pch_compiler.num_outputs, 2)
        self.assertEqual(cc.linker('executable').num_outputs, 1)
        self.assertEqual(cc.linker('shared_library').num_outputs, 2)

        self.assertEqual(cc.compiler.deps_flavor, 'msvc')
        self.assertEqual(cc.pch_compiler.deps_flavor, 'msvc')

        self.assertEqual(cc.compiler.depends_on_libs, False)
        self.assertEqual(cc.pch_compiler.depends_on_libs, False)

        self.assertEqual(cc.compiler.accepts_pch, True)
        self.assertEqual(cc.pch_compiler.accepts_pch, False)

    def test_msvc(self):
        version = ('Microsoft (R) C/C++ Optimizing Compiler Version ' +
                   '19.12.25831 for x86')
        with mock.patch('bfg9000.shell.which',
                        lambda *args, **kwargs: ['command']):
            cc = MsvcBuilder(env, 'c++', 'CXX', ['cl'], 'CXXFLAGS', [],
                             version)

        self.assertEqual(cc.brand, 'msvc')
        self.assertEqual(cc.compiler.brand, 'msvc')
        self.assertEqual(cc.pch_compiler.brand, 'msvc')
        self.assertEqual(cc.linker('executable').brand, 'msvc')
        self.assertEqual(cc.linker('shared_library').brand, 'msvc')

        self.assertEqual(cc.version, Version('19.12.25831'))
        self.assertEqual(cc.compiler.version, Version('19.12.25831'))
        self.assertEqual(cc.pch_compiler.version, Version('19.12.25831'))
        self.assertEqual(cc.linker('executable').version,
                         Version('19.12.25831'))
        self.assertEqual(cc.linker('shared_library').version,
                         Version('19.12.25831'))

    def test_unknown_brand(self):
        version = 'unknown'
        with mock.patch('bfg9000.shell.which',
                        lambda *args, **kwargs: ['command']):
            cc = MsvcBuilder(env, 'c++', 'CXX', ['c++'], 'CXXFLAGS', [],
                             version)

        self.assertEqual(cc.brand, 'unknown')
        self.assertEqual(cc.compiler.brand, 'unknown')
        self.assertEqual(cc.pch_compiler.brand, 'unknown')
        self.assertEqual(cc.linker('executable').brand, 'unknown')
        self.assertEqual(cc.linker('shared_library').brand, 'unknown')

        self.assertEqual(cc.version, None)
        self.assertEqual(cc.compiler.version, None)
        self.assertEqual(cc.pch_compiler.version, None)
        self.assertEqual(cc.linker('executable').version, None)
        self.assertEqual(cc.linker('shared_library').version, None)
