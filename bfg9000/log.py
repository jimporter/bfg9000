import colorama
import logging
import os
import sys
import traceback
import warnings
from logging import (getLogger, CRITICAL, ERROR, WARNING, INFO,  # noqa: F401
                     DEBUG)
from traceback import FrameSummary

from .iterutils import tween
from .platforms.host import platform_info
from .safe_str import safe_string


class UserDeprecationWarning(DeprecationWarning):
    pass


def _path_within(path, parent):
    try:
        rel = os.path.relpath(path, parent)
    except ValueError:
        return False
    return not rel.startswith(os.pardir + os.sep)


def _is_user_src(filename):
    # On Windows, always treat paths within Python's exec_prefix as non-user
    # paths. This lets us correctly identify things like runpy.py and
    # setuptools wrappers as non-user.
    if ( platform_info().family == 'windows' and
         _path_within(filename, sys.exec_prefix) ):
        return False
    return not _path_within(filename, os.path.dirname(__file__))


def _filter_stack(stack):
    # Find where the user's stack frames begin and end.
    gen = enumerate(stack)
    for start, line in gen:
        if _is_user_src(line[0]):
            break
    else:
        start = len(stack)

    for end, line in gen:
        if not _is_user_src(line[0]):
            break
    else:
        end = len(stack)

    return stack[:start], stack[start:end], stack[end:]


def _format_stack(stack, user=False):
    if len(stack) == 0:
        return ''

    if user:
        stack = [FrameSummary(os.path.relpath(i.filename), i.lineno, i.name,
                              locals=i.locals, line=i.line) for i in stack]

    # Put the newline at the beginning, since this helps our formatting later.
    return '\n' + ''.join(traceback.format_list(stack)).rstrip()


class StackFilter:
    def __init__(self, has_stack=True):
        self.has_stack = has_stack

    def filter(self, record):
        has_stack = bool((record.exc_info and record.exc_info[0]) or
                         getattr(record, 'show_stack', False))
        return has_stack == self.has_stack


class ColoredStreamHandler(logging.StreamHandler):
    _format_codes = {
        DEBUG: '1;35',
        INFO: '1;34',
        WARNING: '1;33',
        ERROR: '1;31',
        CRITICAL: '1;41;37',
    }

    def format(self, record):
        record.coloredlevel = '\033[{format}m{name}\033[0m'.format(
            format=self._format_codes.get(record.levelno, '1'),
            name=record.levelname.lower()
        )
        return super().format(record)


class StackfulStreamHandler(ColoredStreamHandler):
    def __init__(self, *args, debug=False, **kwargs):
        self.debug = debug
        super().__init__(*args, **kwargs)

    def emit(self, record):
        if record.exc_info:
            if isinstance(record.exc_info[1], SyntaxError):
                e = record.exc_info[1]
                record.msg = e.msg

                # Figure out where to put the caret.
                text = e.text.expandtabs().rstrip()
                dedent = len(text) - len(text.lstrip())
                offset = 4 - dedent - 1 + e.offset

                record.full_stack = [
                    FrameSummary(e.filename, e.lineno, '<module>',
                                 line=e.text + '\n' + ' ' * offset + '^')
                ]
            else:
                if not record.msg:
                    record.msg = record.exc_info[0].__name__
                elif self.debug:
                    record.msg = '{}: {}'.format(record.exc_info[0].__name__,
                                                 record.msg)
                record.full_stack = traceback.extract_tb(record.exc_info[2])
            record.exc_info = None

        pre, stack, post = _filter_stack(record.full_stack)

        record.stack_pre = _format_stack(pre)
        record.stack = _format_stack(stack, user=True)
        record.stack_post = _format_stack(post)

        if len(stack):
            record.user_pathname = os.path.relpath(stack[-1][0])
            record.user_lineno = stack[-1][1]
        else:
            record.user_pathname = record.pathname
            record.user_lineno = record.lineno

        if len(stack) or self.debug:
            return super().emit(record)

        record.show_stack = False
        logging.root.handle(record)


def _clicolor(environ):
    if environ.get('CLICOLOR_FORCE', '0') != '0':
        return 'always'
    if 'CLICOLOR' in environ:
        return 'never' if environ['CLICOLOR'] == '0' else 'auto'
    return None


def _init_logging(logger, debug, stream=None):
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    stackless = ColoredStreamHandler(stream)
    stackless.addFilter(StackFilter(has_stack=False))

    fmt = '%(coloredlevel)s: %(message)s'

    stackless.setFormatter(logging.Formatter(fmt))
    logger.addHandler(stackless)

    stackful = StackfulStreamHandler(stream, debug=debug)
    stackful.addFilter(StackFilter(has_stack=True))

    fmt = '%(coloredlevel)s: %(user_pathname)s:%(user_lineno)d: %(message)s'
    if debug:
        fmt += '\033[90m%(stack_pre)s\033[0m'
    fmt += '%(stack)s'
    if debug:
        fmt += '\033[90m%(stack_post)s\033[0m'

    stackful.setFormatter(logging.Formatter(fmt))
    logger.addHandler(stackful)


def init(color='auto', debug=False, warn_once=False, environ=os.environ):
    color = _clicolor(environ) or color
    if color == 'always':
        colorama.init(strip=False)
    elif color == 'never':
        colorama.init(strip=True, convert=False)
    else:  # color == 'auto'
        colorama.init()

    warnings.filterwarnings('default', category=UserDeprecationWarning)
    if warn_once:
        warnings.filterwarnings('once')

    _init_logging(logging.root, debug)


def log_stack(level, message, *args, logger=logging, stacklevel=0,
              show_stack=True, **kwargs):
    extra = {
        'full_stack': traceback.extract_stack()[1:-1 - stacklevel],
        'show_stack': show_stack
    }
    logger.log(level, message, *args, extra=extra, **kwargs)


def format_message(*args):
    def str_implemented(s):
        try:
            str(s)
            return True
        except NotImplementedError:
            return False

    message = ''
    for i in tween(args, ' '):
        if isinstance(i, safe_string) and not str_implemented(i):
            message += repr(i)
        else:
            message += str(i)
    return message


def log_message(level, *args, logger=logging, stacklevel=0, **kwargs):
    stacklevel += 1
    log_stack(level, format_message(*args), logger=logger,
              stacklevel=stacklevel, **kwargs)


def info(*args, show_stack=False):
    log_message(INFO, *args, show_stack=show_stack, stacklevel=1)


def debug(*args, show_stack=True):
    log_message(DEBUG, *args, show_stack=show_stack, stacklevel=1)


def _showwarning(message, category, filename, lineno, file=None, line=None):
    # Python 3.6 changes how stacklevel is counted.
    stacklevel = 2 if sys.version_info >= (3, 6) else 1
    log_stack(WARNING, message, stacklevel=stacklevel)


warnings.showwarning = _showwarning
