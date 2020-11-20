from collections import namedtuple
from unittest import mock

from .. import *

from bfg9000.languages import known_langs
from bfg9000.tools import rc

MockPlatform = namedtuple('MockPlatform', ['family'])


def mock_execute_cc(args, **kwargs):
    if args[-1] == '--version':
        return 'version\n'
    elif args[-1] == '-Wl,--version':
        return '', ('COLLECT_GCC=g++\n/usr/bin/collect2 --version\n' +
                    '/usr/bin/ld --version\n')
    elif args[-1] == '-print-search-dirs':
        return 'libraries: =/lib/search/dir1:/lib/search/dir2\n'
    elif args[-1] == '-print-sysroot':
        return '/'
    elif args[-1] == '--verbose':
        return 'SEARCH_DIR("/usr")\n'
    raise OSError('bad option')


def mock_execute_msvc(args, **kwargs):
    if args[-1] == '-?':
        return 'Microsoft (R) Windows (R) Resource Compiler Version 10.0'
    raise OSError('bad option')


class TestRcBuilder(TestCase):
    def test_implicit_linux(self):
        env = make_env(platform='linux', clear_variables=True)
        with mock.patch('bfg9000.tools.rc.choose_builder') as m, \
             mock.patch('bfg9000.shell.which', return_value=['cmd']), \
             mock.patch('bfg9000.shell.execute', mock_execute_cc):  # noqa
            rc.rc_builder(env)
            m.assert_called_once_with(env, known_langs['rc'], rc._builders,
                                      candidates=['windres'])

    def test_implicit_windows(self):
        env = make_env(platform='winnt', clear_variables=True)
        with mock.patch('bfg9000.tools.rc.choose_builder') as m, \
             mock.patch('bfg9000.shell.which', return_value=['cmd']), \
             mock.patch('bfg9000.shell.execute', mock_execute_msvc):  # noqa
            rc.rc_builder(env)
            m.assert_called_once_with(env, known_langs['rc'], rc._builders,
                                      candidates=['rc', 'windres'])

    def test_explicit(self):
        env = make_env(platform='linux', clear_variables=True,
                       variables={'RC': 'gcc-windres'})
        with mock.patch('bfg9000.tools.rc.choose_builder') as m:
            rc.rc_builder(env)
            m.assert_called_once_with(env, known_langs['rc'], rc._builders,
                                      candidates='gcc-windres')

    def test_guess_sibling(self):
        env = make_env(platform='linux', clear_variables=True,
                       variables={'CC': 'gcc-99'})
        with mock.patch('bfg9000.tools.rc.choose_builder') as m, \
             mock.patch('bfg9000.shell.which', return_value=['gcc-99']), \
             mock.patch('bfg9000.shell.execute', mock_execute_cc), \
             mock.patch('bfg9000.log.info'):  # noqa
            rc.rc_builder(env)
            m.assert_called_once_with(env, known_langs['rc'], rc._builders,
                                      candidates='windres-99', strict=True)

    def test_guess_sibling_nonexist(self):
        env = make_env(platform='linux', clear_variables=True,
                       variables={'CC': 'gcc-99'})
        with mock.patch('bfg9000.tools.rc.choose_builder') as m, \
             mock.patch('bfg9000.shell.which', side_effect=IOError()), \
             mock.patch('bfg9000.log.info'), \
             mock.patch('warnings.warn'):  # noqa
            rc.rc_builder(env)
            m.assert_called_once_with(env, known_langs['rc'], rc._builders,
                                      candidates='windres-99', strict=True)

    def test_guess_sibling_indirect(self):
        env = make_env(platform='linux', clear_variables=True,
                       variables={'CXX': 'g++-99'})
        with mock.patch('bfg9000.tools.rc.choose_builder') as m, \
             mock.patch('bfg9000.shell.which', return_value=['gcc-99']), \
             mock.patch('bfg9000.shell.execute', mock_execute_cc), \
             mock.patch('bfg9000.log.info'):  # noqa
            rc.rc_builder(env)
            m.assert_called_once_with(env, known_langs['rc'], rc._builders,
                                      candidates='windres-99', strict=True)

    def test_guess_sibling_matches_default(self):
        env = make_env(platform='linux', clear_variables=True,
                       variables={'CC': 'gcc'})
        with mock.patch('bfg9000.tools.rc.choose_builder') as m, \
             mock.patch('bfg9000.shell.which', return_value=['gcc']), \
             mock.patch('bfg9000.shell.execute', mock_execute_cc), \
             mock.patch('bfg9000.log.info'):  # noqa
            rc.rc_builder(env)
            m.assert_called_once_with(env, known_langs['rc'], rc._builders,
                                      candidates=['windres'])

    def test_guess_sibling_error(self):
        def mock_choose_builder(*args, strict=False, **kwargs):
            if strict:
                raise IOError('bad')
            return mock.MagicMock()

        env = make_env(platform='linux', clear_variables=True,
                       variables={'CC': 'gcc-99'})
        with mock.patch('bfg9000.tools.rc.choose_builder',
                        side_effect=mock_choose_builder) as m, \
             mock.patch('bfg9000.log.info'), \
             mock.patch('warnings.warn'):  # noqa
            rc.rc_builder(env)
            self.assertEqual(m.mock_calls, [
                mock.call(env, known_langs['rc'], rc._builders,
                          candidates='windres-99', strict=True),
                mock.call(env, known_langs['rc'], rc._builders,
                          candidates=['windres']),
            ])
