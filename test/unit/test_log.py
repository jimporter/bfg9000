import logging
import mock
import re
import sys
import traceback
import unittest
from six import assertRegex

from bfg9000 import log, iterutils

# Make sure we're referring to the .py file, not the .pyc file.
this_file = __file__.rstrip('c')


class TestStackfulStreamHandler(unittest.TestCase):
    def test_runtime_error(self):
        handler = log.StackfulStreamHandler()
        try:
            raise RuntimeError('runtime error')
        except RuntimeError:
            record = logging.LogRecord(
                'name', 'level', 'pathname', 1, 'msg', [], sys.exc_info()
            )
        with mock.patch.object(logging.StreamHandler, 'emit'):
            handler.emit(record)

        self.assertEqual(record.full_stack, [
            (this_file, 19, 'test_runtime_error',
             "raise RuntimeError('runtime error')"),
        ])
        self.assertEqual(record.stack_pre, '')
        self.assertEqual(record.stack, (
            '\n' +
            '  File "{}", line 19, in test_runtime_error\n' +
            "    raise RuntimeError('runtime error')"
        ).format(this_file))
        self.assertEqual(record.stack_post, '')
        self.assertEqual(record.user_pathname, this_file)
        self.assertEqual(record.user_lineno, 19)

    def test_internal_error(self):
        handler = log.StackfulStreamHandler()
        try:
            iterutils.first(None)
        except LookupError:
            record = logging.LogRecord(
                'name', 'level', 'pathname', 1, 'msg', [], sys.exc_info()
            )
        with mock.patch.object(logging.StreamHandler, 'emit'):
            handler.emit(record)

        iterutils_file = iterutils.__file__.rstrip('c')
        self.assertEqual(record.full_stack, [
            (this_file, 44, 'test_internal_error', "iterutils.first(None)"),
            (iterutils_file, 48, 'first', 'raise LookupError()'),
        ])
        self.assertEqual(record.stack_pre, '')
        self.assertEqual(record.stack, (
            '\n' +
            '  File "{}", line 44, in test_internal_error\n' +
            "    iterutils.first(None)"
        ).format(this_file))
        self.assertEqual(record.stack_post, (
            '\n' +
            '  File "{}", line 48, in first\n' +
            "    raise LookupError()"
        ).format(iterutils_file))
        self.assertEqual(record.user_pathname, this_file)
        self.assertEqual(record.user_lineno, 44)

    def test_syntax_error(self):
        handler = log.StackfulStreamHandler()
        try:
            raise SyntaxError('syntax error', ('file.py', 1, 4, 'line\n'))
        except SyntaxError:
            record = logging.LogRecord(
                'name', 'level', 'pathname', 1, 'msg', [], sys.exc_info()
            )
        with mock.patch.object(logging.StreamHandler, 'emit'):
            handler.emit(record)

        self.assertEqual(record.full_stack, [
            ('file.py', 1, '<module>', 'line\n       ^'),
        ])
        self.assertEqual(record.stack_pre, '')
        self.assertEqual(record.stack,
                         '\n' +
                         '  File "file.py", line 1, in <module>\n' +
                         '    line\n' +
                         '       ^')
        self.assertEqual(record.stack_post, '')
        self.assertEqual(record.user_pathname, 'file.py')
        self.assertEqual(record.user_lineno, 1)

    def test_no_user_stack(self):
        handler = log.StackfulStreamHandler()
        try:
            iterutils.first(None)
        except LookupError:
            exc = sys.exc_info()
            record = logging.LogRecord(
                'name', 'level', 'pathname', 1, 'msg', [],
                exc[0:2] + (exc[2].tb_next,)
            )
        with mock.patch.object(logging.StreamHandler, 'emit'), \
             mock.patch('logging.root.handle'):  # noqa
            handler.emit(record)

        iterutils_file = iterutils.__file__.rstrip('c')
        self.assertEqual(record.full_stack, [
            (iterutils_file, 48, 'first', 'raise LookupError()'),
        ])
        self.assertEqual(record.stack, (
            '\n' +
            '  File "{}", line 48, in first\n' +
            "    raise LookupError()"
        ).format(iterutils_file))

        self.assertFalse(hasattr(record, 'stack_pre'))
        self.assertFalse(hasattr(record, 'stack_post'))
        self.assertFalse(hasattr(record, 'user_pathname'))
        self.assertFalse(hasattr(record, 'user_lineno'))


class TestInit(unittest.TestCase):
    def test_colors(self):
        with mock.patch('logging.addLevelName'), \
             mock.patch('logging.root.addHandler'):  # noqa
            with mock.patch('colorama.init') as colorama:
                log.init()
                colorama.assert_called_once_with()

            with mock.patch('colorama.init') as colorama:
                log.init(color='always')
                colorama.assert_called_once_with(strip=False)

            with mock.patch('colorama.init') as colorama:
                log.init(color='never')
                colorama.assert_called_once_with(strip=True, convert=False)

    def test_warn_once(self):
        with mock.patch('logging.addLevelName'), \
             mock.patch('logging.root.addHandler'), \
             mock.patch('colorama.init'):  # noqa
            with mock.patch('warnings.filterwarnings') as filterwarnings:
                log.init()
                filterwarnings.assert_not_called()

            with mock.patch('warnings.filterwarnings') as filterwarnings:
                log.init(warn_once=True)
                filterwarnings.assert_called_once_with('once')
