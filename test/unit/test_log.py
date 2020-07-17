import inspect
import logging
import sys
import traceback
import warnings
from io import StringIO
from unittest import mock

from . import *

from bfg9000 import log, iterutils
from bfg9000.path import Path
from bfg9000.safe_str import safe_string

# Make sure we're referring to the .py file, not the .pyc file.
this_file = __file__.rstrip('c')


def current_lineno():
    return inspect.stack()[1][2]


class TestColoredStreamHandler(TestCase):
    def setUp(self):
        self.handler = log.ColoredStreamHandler()
        fmt = '%(coloredlevel)s: %(message)s'
        self.handler.setFormatter(logging.Formatter(fmt))

    def test_info(self):
        record = logging.LogRecord(
            'name', log.INFO, 'pathname', 1, 'message', [], None
        )
        self.assertEqual(self.handler.format(record),
                         '\033[1;34minfo\033[0m: message')

    def test_unknown_level(self):
        record = logging.LogRecord(
            'name', 'unknown', 'pathname', 1, 'message', [], None
        )
        self.assertEqual(self.handler.format(record),
                         '\033[1mlevel unknown\033[0m: message')


class TestStackfulStreamHandler(TestCase):
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
            (iterutils_file, 74, 'first', 'raise LookupError()'),
        ])
        self.assertEqual(record.stack_pre, '')
        self.assertEqual(record.stack, (
            '\n' +
            '  File "{}", line {}, in test_internal_error\n' +
            "    iterutils.first(None)"
        ).format(this_file, lineno))
        self.assertEqual(record.stack_post, (
            '\n' +
            '  File "{}", line 74, in first\n' +
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
            (iterutils_file, 74, 'first', 'raise LookupError()'),
        ])

        self.assertEqual(record.show_stack, False)
        self.assertEqual(record.stack_pre, (
            '\n' +
            '  File "{}", line 74, in first\n' +
            "    raise LookupError()"
        ).format(iterutils_file))
        self.assertEqual(record.stack, '')
        self.assertEqual(record.stack_post, '')
        self.assertEqual(record.user_pathname, record.pathname)
        self.assertEqual(record.user_lineno, record.lineno)

    def test_different_drives(self):
        handler = log.StackfulStreamHandler()
        try:
            lineno = current_lineno() + 1
            raise RuntimeError('runtime error')
        except RuntimeError:
            record = logging.LogRecord(
                'name', 'level', 'pathname', 1, 'msg', [], sys.exc_info()
            )

        # Test with `os.path.relpath` raising a `ValueError` to match what
        # happens when the two paths passed to it are on different drives.
        with mock.patch.object(logging.StreamHandler, 'emit'), \
             mock.patch('os.path.relpath', side_effect=ValueError()):  # noqa
            handler.emit(record)

        self.assertEqual(record.full_stack, [
            (this_file, lineno, 'test_different_drives',
             "raise RuntimeError('runtime error')"),
        ])
        self.assertEqual(record.stack_pre, '')
        self.assertEqual(record.stack, (
            '\n' +
            '  File "{}", line {}, in test_different_drives\n' +
            "    raise RuntimeError('runtime error')"
        ).format(this_file, lineno))
        self.assertEqual(record.stack_post, '')
        self.assertEqual(record.user_pathname, this_file)
        self.assertEqual(record.user_lineno, lineno)


class TestFormatMessage(TestCase):
    def test_str(self):
        self.assertEqual(log.format_message('foo'), 'foo')

    def test_int(self):
        self.assertEqual(log.format_message(1), '1')

    def test_path(self):
        self.assertEqual(log.format_message(Path('path')),
                         repr(Path('path')))

    def test_safe_str(self):
        class StrImplemented(safe_string):
            def __str__(self):
                return 'foo'

            def __repr__(self):
                return 'bar'

        class StrUnimplemented(safe_string):
            def __repr__(self):
                return 'bar'

        self.assertEqual(log.format_message(StrImplemented()), 'foo')
        self.assertEqual(log.format_message(StrUnimplemented()), 'bar')

    def test_many(self):
        self.assertEqual(log.format_message('foo', 1, Path('path'), 'bar'),
                         'foo 1 ' + repr(Path('path')) + ' bar')


class TestLogStack(TestCase):
    def test_default(self):
        with mock.patch('logging.log') as mocklog:
            log.log_stack(log.INFO, 'message')
            tb = traceback.extract_stack()[1:]
            tb[-1].lineno -= 1

            mocklog.assert_called_once_with(
                log.INFO, 'message',
                extra={'full_stack': tb, 'show_stack': True}
            )

        with mock.patch('logging.log') as mocklog:
            log.log_message(log.INFO, 'foo', 1, Path('path'), 'bar')
            tb = traceback.extract_stack()[1:]
            tb[-1].lineno -= 1

            mocklog.assert_called_once_with(
                log.INFO, 'foo 1 ' + repr(Path('path')) + ' bar',
                extra={'full_stack': tb, 'show_stack': True}
            )

    def test_stacklevel(self):
        with mock.patch('logging.log') as mocklog:
            log.log_stack(log.INFO, 'message', stacklevel=1)
            tb = traceback.extract_stack()[1:-1]
            mocklog.assert_called_once_with(log.INFO, 'message', extra={
                'full_stack': tb, 'show_stack': True
            })

        with mock.patch('logging.log') as mocklog:
            log.log_message(log.INFO, 'foo', 1, Path('path'), 'bar',
                            stacklevel=1)
            tb = traceback.extract_stack()[1:-1]
            mocklog.assert_called_once_with(
                log.INFO, 'foo 1 ' + repr(Path('path')) + ' bar', extra={
                    'full_stack': tb, 'show_stack': True
                }
            )

    def test_hide_stack(self):
        with mock.patch('logging.log') as mocklog:
            log.log_stack(log.INFO, 'message', show_stack=False)
            tb = traceback.extract_stack()[1:]
            tb[-1].lineno -= 1

            mocklog.assert_called_once_with(log.INFO, 'message', extra={
                'full_stack': tb, 'show_stack': False
            })

        with mock.patch('logging.log') as mocklog:
            # Make sure the log_message call is all on one line to avoid
            # differences in how stacks for multi-line statements are handled
            # on various Python versions.
            args = (log.INFO, 'foo', 1, Path('path'), 'bar')
            log.log_message(*args, show_stack=False)
            tb = traceback.extract_stack()[1:]
            tb[-1].lineno -= 1

            mocklog.assert_called_once_with(
                log.INFO, 'foo 1 ' + repr(Path('path')) + ' bar', extra={
                    'full_stack': tb, 'show_stack': False
                }
            )

    def test_info(self):
        with mock.patch('logging.log') as mocklog:
            log.info('message')
            tb = traceback.extract_stack()[1:]
            tb[-1].lineno -= 1

            mocklog.assert_called_once_with(log.INFO, 'message', extra={
                'full_stack': tb, 'show_stack': False
            })

        with mock.patch('logging.log') as mocklog:
            log.info('foo', 1, Path('path'), 'bar')
            tb = traceback.extract_stack()[1:]
            tb[-1].lineno -= 1

            mocklog.assert_called_once_with(
                log.INFO, 'foo 1 ' + repr(Path('path')) + ' bar', extra={
                    'full_stack': tb, 'show_stack': False
                }
            )

        for show_stack in (False, True):
            with mock.patch('logging.log') as mocklog:
                log.info('message', show_stack=show_stack)
                tb = traceback.extract_stack()[1:]
                tb[-1].lineno -= 1

                mocklog.assert_called_once_with(log.INFO, 'message', extra={
                    'full_stack': tb, 'show_stack': show_stack
                })

    def test_debug(self):
        with mock.patch('logging.log') as mocklog:
            log.debug('message')
            tb = traceback.extract_stack()[1:]
            tb[-1].lineno -= 1

            mocklog.assert_called_once_with(log.DEBUG, 'message', extra={
                'full_stack': tb, 'show_stack': True
            })

        with mock.patch('logging.log') as mocklog:
            log.debug('foo', 1, Path('path'), 'bar')
            tb = traceback.extract_stack()[1:]
            tb[-1].lineno -= 1

            mocklog.assert_called_once_with(
                log.DEBUG, 'foo 1 ' + repr(Path('path')) + ' bar', extra={
                    'full_stack': tb, 'show_stack': True
                }
            )

        for show_stack in (False, True):
            with mock.patch('logging.log') as mocklog:
                log.debug('message', show_stack=show_stack)
                tb = traceback.extract_stack()[1:]
                tb[-1].lineno -= 1

                mocklog.assert_called_once_with(log.DEBUG, 'message', extra={
                    'full_stack': tb, 'show_stack': show_stack
                })


class TestLogger(TestCase):
    @staticmethod
    def _level(levelno):
        return '\033[{format}m{name}\033[0m'.format(
            format=log.ColoredStreamHandler._format_codes.get(levelno, '1'),
            name=logging.getLevelName(levelno).lower()
        )

    def setUp(self):
        self.out = StringIO()
        self.logger = log.getLogger(__name__)
        log._init_logging(self.logger, False, self.out)

    def test_info(self):
        log.log_message(log.INFO, 'message', logger=self.logger,
                        show_stack=False)
        self.assertEqual(self.out.getvalue(),
                         '{}: message\n'.format(self._level(log.INFO)))

    def test_exception(self):
        try:
            lineno = current_lineno() + 1
            raise RuntimeError('runtime error')
        except RuntimeError as e:
            self.logger.exception(e)
        self.assertEqual(self.out.getvalue(), (
            '{level}: {file}:{line}: runtime error\n' +
            '  File "{file}", line {line}, in test_exception\n' +
            "    raise RuntimeError('runtime error')\n"
        ).format(level=self._level(log.ERROR), file=this_file, line=lineno))


class TestShowWarning(TestCase):
    def test_warn(self):
        class EqualWarning(UserWarning):
            def __eq__(self, rhs):
                return type(self) == type(rhs)

        with mock.patch('logging.log') as mocklog:
            warnings.warn('message', EqualWarning)

            tb = traceback.extract_stack()[1:]
            tb[-1] = mocklog.call_args[1]['extra']['full_stack'][-1]
            mocklog.assert_called_once_with(
                log.WARNING, EqualWarning('message'), extra={
                    'full_stack': tb, 'show_stack': True
                }
            )


class TestInit(TestCase):
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
