import mock
import unittest
from six import assertRaisesRegex

from bfg9000.environment import Environment
from bfg9000.languages import Languages
from bfg9000.tools import cc, common

known_langs = Languages()
with known_langs.make('c') as x:
    x.vars(compiler='CC', cflags='CFLAGS')


def mock_which(*args, **kwargs):
    return ['command']


def mock_execute(args, **kwargs):
    if args[-1] == '--version':
        return ('g++ (Ubuntu 5.4.0-6ubuntu1~16.04.6) 5.4.0 20160609\n' +
                'Copyright (C) 2015 Free Software Foundation, Inc.')
    elif args[-1] == '-Wl,--version':
        return '', '/usr/bin/ld --version\n'
    elif args[-1] == '-print-search-dirs':
        return 'libraries: =/lib/search/dir1:/lib/search/dir2\n'
    elif args[-1] == '-print-sysroot':
        return '/'
    elif args[-1] == '--verbose':
        return 'SEARCH_DIR("/usr")\n'


class TestChooseBuilder(unittest.TestCase):
    def setUp(self):
        self.env = Environment(None, None, None, None, None, {},
                               (False, False), None)
        self.env.variables = {}

    def test_choose(self):
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            builder = common.choose_builder(self.env, known_langs['c'], 'cc',
                                            (cc.CcBuilder, ))
        self.assertEqual(builder.brand, 'gcc')

    def test_not_found(self):
        def bad_which(*args, **kwargs):
            if args[0] == ['cc']:
                raise IOError('badness')
            else:
                return mock_which(*args, **kwargs)

        with mock.patch('bfg9000.shell.which', bad_which), \
             mock.patch('bfg9000.shell.execute', mock_execute), \
             mock.patch('warnings.warn', lambda s: None):  # noqa
            builder = common.choose_builder(self.env, known_langs['c'], 'cc',
                                            (cc.CcBuilder, ))
        self.assertEqual(builder.brand, 'unknown')

    def test_nonworking(self):
        def bad_execute(args, **kwargs):
            raise ValueError()

        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', bad_execute):  # noqa
            msg = "^no working c compiler found; tried 'cc'$"
            with assertRaisesRegex(self, IOError, msg):
                common.choose_builder(self.env, known_langs['c'], 'cc',
                                      (cc.CcBuilder, ))
