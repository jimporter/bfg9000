import inspect
import logging
import mock
import re
import sys
import traceback
import unittest
import warnings
from six import assertRegex

from bfg9000 import log, iterutils

# Make sure we're referring to the .py file, not the .pyc file.
this_file = __file__.rstrip('c')


def current_lineno():
    return inspect.stack()[1][2]


class TestStackfulStreamHandler(unittest.TestCase):
    def test_runtime_error(self):
        handler = log.StackfulStreamHandler()
        try:
            lineno = current_lineno() + 1
            raise RuntimeError('runtime error')
        except RuntimeError:
            record = logging.LogRecord(
                'name', 'level', 'pathname', 1, 'msg', [], sys.exc_info()
            )
        with mock.patch.object(logging.StreamHandler, 'emit'):
            handler.emit(record)

        self.assertEqual(record.full_stack, [
            (this_file, lineno, 'test_runtime_error',
             "raise RuntimeError('runtime error')"),
        ])
        self.assertEqual(record.stack_pre, '')
        self.assertEqual(record.stack, (
            '\n' +
            '  File "{}", line {}, in test_runtime_error\n' +
            "    raise RuntimeError('runtime error')"
        ).format(this_file, lineno))
        self.assertEqual(record.stack_post, '')
        self.assertEqual(record.user_pathname, this_file)
        self.assertEqual(record.user_lineno, lineno)

    def test_internal_error(self):
        handler = log.StackfulStreamHandler()
        try:
            lineno = current_lineno() + 1
            iterutils.first(None)
        except LookupError:
            record = logging.LogRecord(
                'name', 'level', 'pathname', 1, 'msg', [], sys.exc_info()
            )
        with mock.patch.object(logging.StreamHandler, 'emit'):
            handler.emit(record)

        iterutils_file = iterutils.__file__.rstrip('c')
        self.assertEqual(record.full_stack, [
            (this_file, lineno, 'test_internal_error',
             "iterutils.first(None)"),
            (iterutils_file, 48, 'first', 'raise LookupError()'),
        ])
        self.assertEqual(record.stack_pre, '')
        self.assertEqual(record.stack, (
            '\n' +
            '  File "{}", line {}, in test_internal_error\n' +
            "    iterutils.first(None)"
        ).format(this_file, lineno))
        self.assertEqual(record.stack_post, (
            '\n' +
            '  File "{}", line 48, in first\n' +
            "    raise LookupError()"
        ).format(iterutils_file))
        self.assertEqual(record.user_pathname, this_file)
        self.assertEqual(record.user_lineno, lineno)

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


class TestLogStack(unittest.TestCase):
    def test_default(self):
        with mock.patch('logging.log') as mocklog:
            lineno = current_lineno() + 1
            log.log_stack(log.INFO, 'message')

            tb = traceback.extract_stack()[1:]
            tb[-1] = (tb[-1][0], lineno, tb[-1][2],
                      "log.log_stack(log.INFO, 'message')")
            mocklog.assert_called_once_with(log.INFO, 'message', extra={
                'full_stack': tb, 'show_stack': True
            })

    def test_stacklevel(self):
        with mock.patch('logging.log') as mocklog:
            log.log_stack(log.INFO, 'message', stacklevel=1)
            tb = traceback.extract_stack()[1:-1]
            mocklog.assert_called_once_with(log.INFO, 'message', extra={
                'full_stack': tb, 'show_stack': True
            })

    def test_hide_stack(self):
        with mock.patch('logging.log') as mocklog:
            lineno = current_lineno() + 1
            log.log_stack(log.INFO, 'message', show_stack=False)

            tb = traceback.extract_stack()[1:]
            tb[-1] = (tb[-1][0], lineno, tb[-1][2],
                      "log.log_stack(log.INFO, 'message', show_stack=False)")
            mocklog.assert_called_once_with(log.INFO, 'message', extra={
                'full_stack': tb, 'show_stack': False
            })


class TestShowWarning(unittest.TestCase):
    def test_warn(self):
        with mock.patch('logging.log') as mocklog:
            class EqualWarning(UserWarning):
                def __eq__(self, rhs):
                    return type(self) == type(rhs)

            lineno = current_lineno() + 1
            warnings.warn('message', EqualWarning)

            tb = traceback.extract_stack()[1:]
            tb[-1] = (tb[-1][0], lineno, tb[-1][2],
                      "warnings.warn('message', EqualWarning)")
            mocklog.assert_called_once_with(
                log.WARNING, EqualWarning('message'), extra={
                    'full_stack': tb, 'show_stack': True
                }
            )


class TestInit(unittest.TestCase):
    def test_colors(self):
        with mock.patch('logging.addLevelName'), \
             mock.patch('logging.root.addHandler'), \
             mock.patch('logging.root.setLevel'):  # noqa
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
             mock.patch('logging.root.setLevel'), \
             mock.patch('colorama.init'):  # noqa
            with mock.patch('warnings.filterwarnings') as filterwarnings:
                log.init()
                filterwarnings.assert_called_once_with(
                    'default', category=log.UserDeprecationWarning
                )

            with mock.patch('warnings.filterwarnings') as filterwarnings:
                log.init(warn_once=True)
                self.assertEqual(filterwarnings.mock_calls, [
                    mock.call('default', category=log.UserDeprecationWarning),
                    mock.call('once')
                ])

    def test_debug(self):
        with mock.patch('logging.addLevelName'), \
             mock.patch('logging.root.addHandler'), \
             mock.patch('colorama.init'):  # noqa
            with mock.patch('logging.root.setLevel') as setLevel:
                log.init()
                setLevel.assert_called_once_with(log.INFO)

            with mock.patch('logging.root.setLevel') as setLevel:
                log.init(debug=True)
                setLevel.assert_called_once_with(log.DEBUG)
