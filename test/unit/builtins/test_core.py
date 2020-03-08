import logging
import traceback
from unittest import mock

from .common import BuiltinTest
from bfg9000.builtins import core  # noqa
from bfg9000 import exceptions
from bfg9000.path import Path, Root
from bfg9000.safe_str import safe_str, safe_format


class TestCore(BuiltinTest):
    def test_warning(self):
        with mock.patch('warnings.warn') as warn:
            self.context['warning']('message')
            warn.assert_called_once_with('message')

        with mock.patch('warnings.warn') as warn:
            self.context['warning']('message', 1, Path('path'), 'bar')
            warn.assert_called_once_with(
                'message 1 ' + repr(Path('path')) + ' bar'
            )

    def test_info(self):
        with mock.patch('logging.log') as log:
            self.context['info']('message')
            tb = traceback.extract_stack()[1:]
            tb[-1].lineno -= 1

            log.assert_called_once_with(logging.INFO, 'message', extra={
                'full_stack': tb, 'show_stack': False
            })

        with mock.patch('logging.log') as log:
            self.context['info']('message', 1, Path('path'), 'bar')
            tb = traceback.extract_stack()[1:]
            tb[-1].lineno -= 1

            log.assert_called_once_with(
                logging.INFO, 'message 1 ' + repr(Path('path')) + ' bar',
                extra={
                    'full_stack': tb, 'show_stack': False
                }
            )

        with mock.patch('logging.log') as log:
            self.context['info']('message', show_stack=True)
            tb = traceback.extract_stack()[1:]
            tb[-1].lineno -= 1

            log.assert_called_once_with(logging.INFO, 'message', extra={
                'full_stack': tb, 'show_stack': True
            })

    def test_debug(self):
        with mock.patch('logging.log') as log:
            self.context['debug']('message')
            tb = traceback.extract_stack()[1:]
            tb[-1].lineno -= 1

            log.assert_called_once_with(logging.DEBUG, 'message', extra={
                'full_stack': tb, 'show_stack': True
            })

        with mock.patch('logging.log') as log:
            self.context['debug']('message', 1, Path('path'), 'bar')
            tb = traceback.extract_stack()[1:]
            tb[-1].lineno -= 1

            log.assert_called_once_with(
                logging.DEBUG, 'message 1 ' + repr(Path('path')) + ' bar',
                extra={
                    'full_stack': tb, 'show_stack': True
                }
            )

        with mock.patch('logging.log') as log:
            self.context['debug']('message', show_stack=False)
            tb = traceback.extract_stack()[1:]
            tb[-1].lineno -= 1

            log.assert_called_once_with(logging.DEBUG, 'message', extra={
                'full_stack': tb, 'show_stack': False
            })

    def test_exceptions(self):
        for name in dir(exceptions):
            t = getattr(exceptions, name)
            if isinstance(t, type):
                self.assertIs(self.context[name], t)

    def test_safe_str(self):
        self.assertIs(self.context['safe_str'], safe_str)
        self.assertIs(self.context['safe_format'], safe_format)

    def test_submodule(self):
        def mock_execute(context, path):
            return context.PathEntry(path)

        with mock.patch('bfg9000.build.execute_file',
                        mock.MagicMock(wraps=mock_execute)) as m:
            self.assertEqual(self.context['submodule']('dir'), {})
            m.assert_called_once_with(self.context,
                                      Path('dir/build.bfg', Root.srcdir))

        with self.context.push_path(Path('dir/build.bfg', Root.srcdir)), \
             mock.patch('bfg9000.build.execute_file',
                        mock.MagicMock(wraps=mock_execute)) as m:  # noqa
            self.assertEqual(self.context['submodule']('sub'), {})
            m.assert_called_once_with(self.context,
                                      Path('dir/sub/build.bfg', Root.srcdir))

    def test_export(self):
        with self.context.push_path(Path('foo/build.bfg', Root.srcdir)) as p:
            self.context['export'](foo='foo')
        self.assertEqual(p.exports, {'foo': 'foo'})
        self.assertRaises(ValueError, self.context['export'], bar='bar')
