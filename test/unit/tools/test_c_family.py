from collections import namedtuple
from unittest import mock

from .. import *

from bfg9000.languages import known_langs
from bfg9000.tools import c_family

MockPlatform = namedtuple('MockPlatform', ['family'])


class MockEnv:
    def __init__(self, *args, host_platform='posix', **kwargs):
        self.host_platform = MockPlatform(host_platform)
        self.variables = dict(*args, **kwargs)

    def getvar(self, *args, **kwargs):
        return self.variables.get(*args, **kwargs)


class TestGuessCandidates(TestCase):
    def test_cxx_from_cc(self):
        guess_candidates = c_family._guess_candidates
        self.assertEqual(guess_candidates(MockEnv(CC='cc'), 'c++'),
                         [('c', 'cc', 'c++')])
        self.assertEqual(guess_candidates(MockEnv(CC='gcc'), 'c++'),
                         [('c', 'gcc', 'g++')])
        self.assertEqual(guess_candidates(MockEnv(CC='clang'), 'c++'),
                         [('c', 'clang', 'clang++')])
        self.assertEqual(guess_candidates(MockEnv(CC='gcc-9'), 'c++'),
                         [('c', 'gcc-9', 'g++-9')])

        mingw = 'x86_64-w64-mingw32-'
        self.assertEqual(guess_candidates(MockEnv(CC=mingw + 'gcc'), 'c++'),
                         [('c', mingw + 'gcc', mingw + 'g++')])
        self.assertEqual(guess_candidates(MockEnv(CC=mingw + 'gcc-9'), 'c++'),
                         [('c', mingw + 'gcc-9', mingw + 'g++-9')])

    def test_c_from_cxx(self):
        guess_candidates = c_family._guess_candidates
        self.assertEqual(guess_candidates(MockEnv(CXX='c++'), 'c'),
                         [('c++', 'c++', 'cc')])
        self.assertEqual(guess_candidates(MockEnv(CXX='g++'), 'c'),
                         [('c++', 'g++', 'gcc')])
        self.assertEqual(guess_candidates(MockEnv(CXX='clang++'), 'c'),
                         [('c++', 'clang++', 'clang')])
        self.assertEqual(guess_candidates(MockEnv(CXX='g++-9'), 'c'),
                         [('c++', 'g++-9', 'gcc-9')])

        mingw = 'x86_64-w64-mingw32-'
        self.assertEqual(guess_candidates(MockEnv(CXX=mingw + 'g++'), 'c'),
                         [('c++', mingw + 'g++', mingw + 'gcc')])
        self.assertEqual(guess_candidates(MockEnv(CXX=mingw + 'g++-9'), 'c'),
                         [('c++', mingw + 'g++-9', mingw + 'gcc-9')])

    def test_objc_from_cc(self):
        guess_candidates = c_family._guess_candidates
        self.assertEqual(guess_candidates(MockEnv(CC='cc'), 'objc'),
                         [('c', 'cc', 'cc')])
        self.assertEqual(guess_candidates(MockEnv(CC='gcc'), 'objc'),
                         [('c', 'gcc', 'gcc')])
        self.assertEqual(guess_candidates(MockEnv(CC='clang'), 'objc'),
                         [('c', 'clang', 'clang')])
        self.assertEqual(guess_candidates(MockEnv(CC='gcc-9'), 'objc'),
                         [('c', 'gcc-9', 'gcc-9')])

        mingw = 'x86_64-w64-mingw32-'
        self.assertEqual(guess_candidates(MockEnv(CC=mingw + 'gcc'), 'objc'),
                         [('c', mingw + 'gcc', mingw + 'gcc')])
        self.assertEqual(guess_candidates(MockEnv(CC=mingw + 'gcc-9'), 'objc'),
                         [('c', mingw + 'gcc-9', mingw + 'gcc-9')])

    def test_objcxx_from_cxx(self):
        guess_candidates = c_family._guess_candidates
        self.assertEqual(guess_candidates(MockEnv(CXX='c++'), 'objc++'),
                         [('c++', 'c++', 'c++')])
        self.assertEqual(guess_candidates(MockEnv(CXX='g++'), 'objc++'),
                         [('c++', 'g++', 'g++')])
        self.assertEqual(guess_candidates(MockEnv(CXX='clang++'), 'objc++'),
                         [('c++', 'clang++', 'clang++')])
        self.assertEqual(guess_candidates(MockEnv(CXX='g++-9'), 'objc++'),
                         [('c++', 'g++-9', 'g++-9')])

        mingw = 'x86_64-w64-mingw32-'
        self.assertEqual(guess_candidates(MockEnv(CXX=mingw + 'g++'),
                                          'objc++'),
                         [('c++', mingw + 'g++', mingw + 'g++')])
        self.assertEqual(guess_candidates(MockEnv(CXX=mingw + 'g++-9'),
                                          'objc++'),
                         [('c++', mingw + 'g++-9', mingw + 'g++-9')])

    def test_cxx_from_c_cl(self):
        guess_candidates = c_family._guess_candidates
        self.assertEqual(guess_candidates(MockEnv(CC='cl'), 'c++'),
                         [('c', 'cl', 'cl')])
        self.assertEqual(guess_candidates(MockEnv(CC='clang-cl'), 'c++'),
                         [('c', 'clang-cl', 'clang-cl')])
        self.assertEqual(guess_candidates(MockEnv(CC='clang-cl-9'), 'c++'),
                         [('c', 'clang-cl-9', 'clang-cl-9')])

        prefix = 'prefix-'
        self.assertEqual(guess_candidates(MockEnv(CC=prefix + 'cl'), 'c++'),
                         [('c', prefix + 'cl', prefix + 'cl')])
        self.assertEqual(guess_candidates(MockEnv(CC=prefix + 'cl-9'), 'c++'),
                         [('c', prefix + 'cl-9', prefix + 'cl-9')])

    def test_c_from_cxx_cl(self):
        guess_candidates = c_family._guess_candidates
        self.assertEqual(guess_candidates(MockEnv(CXX='cl'), 'c'),
                         [('c++', 'cl', 'cl')])
        self.assertEqual(guess_candidates(MockEnv(CXX='clang-cl'), 'c'),
                         [('c++', 'clang-cl', 'clang-cl')])
        self.assertEqual(guess_candidates(MockEnv(CXX='clang-cl-9'), 'c'),
                         [('c++', 'clang-cl-9', 'clang-cl-9')])

        prefix = 'prefix-'
        self.assertEqual(guess_candidates(MockEnv(CXX=prefix + 'cl'), 'c'),
                         [('c++', prefix + 'cl', prefix + 'cl')])
        self.assertEqual(guess_candidates(MockEnv(CXX=prefix + 'cl-9'), 'c'),
                         [('c++', prefix + 'cl-9', prefix + 'cl-9')])

    def test_cxx_from_multiple(self):
        guess_candidates = c_family._guess_candidates
        env = MockEnv(CC='cc', OBJC='objc-cc', OBJCXX='objcxx-c++')
        self.assertEqual(guess_candidates(env, 'c++'), [
            ('objc++', 'objcxx-c++', 'objcxx-c++'),
            ('c', 'cc', 'c++'),
            ('objc', 'objc-cc', 'objc-c++'),
        ])

    def test_unrecognized(self):
        guess_candidates = c_family._guess_candidates
        self.assertEqual(guess_candidates(MockEnv(CXX='goofy'), 'c'), [])


class TestCFamilyBuilder(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(clear_variables=True, *args, **kwargs)
        if self.platform_name and self.env.host_platform.family == 'windows':
            self.cmds = c_family._windows_cmds
            self.fallback = c_family._fallback_windows_builder
        else:
            self.cmds = c_family._posix_cmds
            self.fallback = c_family._fallback_posix_builder

    def test_fallback_builder(self):
        with mock.patch('bfg9000.shell.which', side_effect=IOError()), \
             mock.patch('warnings.warn'):
            self.assertIsInstance(c_family.c_family_builder(self.env, 'c++'),
                                  self.fallback)

    def test_implicit(self):
        with mock.patch('bfg9000.tools.c_family.choose_builder') as m:
            c_family.c_family_builder(self.env, 'c++')
            m.assert_called_once_with(
                self.env, known_langs['c++'], c_family._builders,
                candidates=self.cmds['c++'], fallback_builder=self.fallback
            )

    def test_explicit(self):
        self.env.variables['CXX'] = 'g++'
        with mock.patch('bfg9000.tools.c_family.choose_builder') as m:
            c_family.c_family_builder(self.env, 'c++')
            m.assert_called_once_with(
                self.env, known_langs['c++'], c_family._builders,
                candidates='g++', fallback_builder=self.fallback
            )

    def test_guess_sibling(self):
        self.env.variables['CC'] = 'gcc'
        with mock.patch('bfg9000.tools.c_family.choose_builder') as m, \
             mock.patch('bfg9000.log.info'):
            c_family.c_family_builder(self.env, 'c++')
            m.assert_called_once_with(
                self.env, known_langs['c++'], c_family._builders,
                candidates='g++', fallback_builder=self.fallback, strict=True
            )

    def test_guess_sibling_matches_default(self):
        self.env.variables['CC'] = self.cmds['c'][0]
        with mock.patch('bfg9000.tools.c_family.choose_builder') as m, \
             mock.patch('bfg9000.log.info'):
            c_family.c_family_builder(self.env, 'c++')
            m.assert_called_once_with(
                self.env, known_langs['c++'], c_family._builders,
                candidates=self.cmds['c++'], fallback_builder=self.fallback
            )

    def test_guess_sibling_error(self):
        def mock_choose_builder(*args, strict=False, **kwargs):
            if strict:
                raise IOError('bad')
            return mock.MagicMock()

        self.env.variables['CC'] = 'gcc'
        with mock.patch('bfg9000.tools.c_family.choose_builder',
                        side_effect=mock_choose_builder) as m, \
             mock.patch('bfg9000.log.info'):
            c_family.c_family_builder(self.env, 'c++')
            cmds = [i for i in self.cmds['c++'] if i != 'g++']
            self.assertEqual(m.mock_calls, [
                mock.call(self.env, known_langs['c++'], c_family._builders,
                          candidates='g++', fallback_builder=self.fallback,
                          strict=True),
                mock.call(self.env, known_langs['c++'], c_family._builders,
                          candidates=cmds, fallback_builder=self.fallback),
            ])
