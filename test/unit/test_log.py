import logging
import mock
import re
import sys
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
            (this_file, 18, 'test_runtime_error',
             "raise RuntimeError('runtime error')"),
        ])
        self.assertEqual(record.stack_pre, '')
        self.assertEqual(record.stack, (
            '\n' +
            '  File "{}", line 18, in test_runtime_error\n' +
            "    raise RuntimeError('runtime error')"
        ).format(this_file))
        self.assertEqual(record.stack_post, '')
        self.assertEqual(record.user_pathname, this_file)
        self.assertEqual(record.user_lineno, 18)

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
            (this_file, 43, 'test_internal_error', "iterutils.first(None)"),
            (iterutils_file, 48, 'first', 'raise LookupError()'),
        ])
        self.assertEqual(record.stack_pre, '')
        self.assertEqual(record.stack, (
            '\n' +
            '  File "{}", line 43, in test_internal_error\n' +
            "    iterutils.first(None)"
        ).format(this_file))
        self.assertEqual(record.stack_post, (
            '\n' +
            '  File "{}", line 48, in first\n' +
            "    raise LookupError()"
        ).format(iterutils_file))
        self.assertEqual(record.user_pathname, this_file)
        self.assertEqual(record.user_lineno, 43)

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
