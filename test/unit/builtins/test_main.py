import logging
import traceback
from unittest import mock

from .common import BuiltinTest
from bfg9000 import builtins
from bfg9000 import exceptions
from bfg9000.builtins.builtin import BuildContext
from bfg9000.path import Path, Root, InstallRoot
from bfg9000.safe_str import safe_str, safe_format


class TestBuiltin(BuiltinTest):
    def test_init(self):
        builtins.init()
        context = BuildContext(self.env, self.build, None)
        self.assertTrue('project' in context.builtins)
        self.assertTrue('executable' in context.builtins)

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

    def test_path(self):
        self.assertIs(self.context['Path'], Path)
        self.assertIs(self.context['Root'], Root)
        self.assertIs(self.context['InstallRoot'], InstallRoot)

    def test_safe_str(self):
        self.assertIs(self.context['safe_str'], safe_str)
        self.assertIs(self.context['safe_format'], safe_format)
