import logging
import mock

from .common import BuiltinTest
from bfg9000 import builtins
from bfg9000 import exceptions


class TestBuiltin(BuiltinTest):
    def test_warning(self):
        with mock.patch('warnings.warn') as warn:
            builtins.warning('message')
            warn.assert_called_once_with('message')

    def test_info(self):
        with mock.patch('logging.log') as log:
            builtins.info('message')
            self.assertEqual(log.call_args[0][0], logging.INFO)
            self.assertEqual(log.call_args[0][1], 'message')
            self.assertEqual(log.call_args[1]['extra']['show_stack'], False)

            builtins.info('message', True)
            self.assertEqual(log.call_args[0][0], logging.INFO)
            self.assertEqual(log.call_args[0][1], 'message')
            self.assertEqual(log.call_args[1]['extra']['show_stack'], True)

    def test_debug(self):
        with mock.patch('logging.log') as log:
            builtins.debug('message')
            self.assertEqual(log.call_args[0][0], logging.DEBUG)
            self.assertEqual(log.call_args[0][1], 'message')
            self.assertEqual(log.call_args[1]['extra']['show_stack'], True)

            builtins.debug('message', False)
            self.assertEqual(log.call_args[0][0], logging.DEBUG)
            self.assertEqual(log.call_args[0][1], 'message')
            self.assertEqual(log.call_args[1]['extra']['show_stack'], False)

    def test_exceptions(self):
        for name in dir(exceptions):
            t = getattr(exceptions, name)
            if isinstance(t, type):
                self.assertTrue(self.builtin_dict[name] is t)
