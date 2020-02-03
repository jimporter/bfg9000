import logging
import traceback
from unittest import mock

from .common import BuiltinTest
from bfg9000 import builtins
from bfg9000 import exceptions
from bfg9000.path import Path, Root, InstallRoot
from bfg9000.safe_str import safe_str, safe_format


class TestBuiltin(BuiltinTest):
    def test_init(self):
        builtins.init()
        builtin_dict = self.bind()
        self.assertTrue('project' in builtin_dict)
        self.assertTrue('executable' in builtin_dict)

    def test_warning(self):
        with mock.patch('warnings.warn') as warn:
            builtins.warning('message')
            warn.assert_called_once_with('message')

        with mock.patch('warnings.warn') as warn:
            builtins.warning('message', 1, Path('path'), 'bar')
            warn.assert_called_once_with(
                'message 1 ' + repr(Path('path')) + ' bar'
            )

    def test_info(self):
        with mock.patch('logging.log') as log:
            builtins.info('message')
            tb = traceback.extract_stack()[1:]
            tb[-1].lineno -= 1

            log.assert_called_once_with(logging.INFO, 'message', extra={
                'full_stack': tb, 'show_stack': False
            })

        with mock.patch('logging.log') as log:
            builtins.info('message', 1, Path('path'), 'bar')
            tb = traceback.extract_stack()[1:]
            tb[-1].lineno -= 1

            log.assert_called_once_with(
                logging.INFO, 'message 1 ' + repr(Path('path')) + ' bar',
                extra={
                    'full_stack': tb, 'show_stack': False
                }
            )

        with mock.patch('logging.log') as log:
            builtins.info('message', show_stack=True)
            tb = traceback.extract_stack()[1:]
            tb[-1].lineno -= 1

            log.assert_called_once_with(logging.INFO, 'message', extra={
                'full_stack': tb, 'show_stack': True
            })

    def test_debug(self):
        with mock.patch('logging.log') as log:
            builtins.debug('message')
            tb = traceback.extract_stack()[1:]
            tb[-1].lineno -= 1

            log.assert_called_once_with(logging.DEBUG, 'message', extra={
                'full_stack': tb, 'show_stack': True
            })

        with mock.patch('logging.log') as log:
            builtins.debug('message', 1, Path('path'), 'bar')
            tb = traceback.extract_stack()[1:]
            tb[-1].lineno -= 1

            log.assert_called_once_with(
                logging.DEBUG, 'message 1 ' + repr(Path('path')) + ' bar',
                extra={
                    'full_stack': tb, 'show_stack': True
                }
            )

        with mock.patch('logging.log') as log:
            builtins.debug('message', show_stack=False)
            tb = traceback.extract_stack()[1:]
            tb[-1].lineno -= 1

            log.assert_called_once_with(logging.DEBUG, 'message', extra={
                'full_stack': tb, 'show_stack': False
            })

    def test_exceptions(self):
        for name in dir(exceptions):
            t = getattr(exceptions, name)
            if isinstance(t, type):
                self.assertIs(self.builtin_dict[name], t)

    def test_path(self):
        self.assertIs(self.builtin_dict['Path'], Path)
        self.assertIs(self.builtin_dict['Root'], Root)
        self.assertIs(self.builtin_dict['InstallRoot'], InstallRoot)

    def test_safe_str(self):
        self.assertIs(self.builtin_dict['safe_str'], safe_str)
        self.assertIs(self.builtin_dict['safe_format'], safe_format)
