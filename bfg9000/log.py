import colorama
import logging
import os
import sys
import traceback
import warnings
from logging import getLogger, CRITICAL, ERROR, WARNING, INFO, DEBUG  # noqa


class UserDeprecationWarning(DeprecationWarning):
    pass


def _is_bfg_src(filename):
    try:
        rel = os.path.relpath(filename, os.path.dirname(__file__))
    except ValueError:
        return False
    return not rel.startswith(os.pardir + os.sep)


def _filter_stack(stack):
    # Find where the user's stack frames begin and end.
    gen = enumerate(stack)
    for start, line in gen:
        if not _is_bfg_src(line[0]):
            break
    else:
        start = len(stack)

    for end, line in gen:
        if _is_bfg_src(line[0]):
            break
    else:
        end = len(stack)

    return stack[:start], stack[start:end], stack[end:]


def _format_stack(stack):
    if len(stack) == 0:
        return ''
    # Put the newline at the beginning, since this helps our formatting later.
    return '\n' + ''.join(traceback.format_list(stack)).rstrip()


class StackFilter(object):
    def __init__(self, has_stack=True):
        self.has_stack = has_stack

    def filter(self, record):
        has_stack = bool((record.exc_info and record.exc_info[0]) or
                         getattr(record, 'show_stack', False))
        return has_stack == self.has_stack


class StackfulStreamHandler(logging.StreamHandler):
    def __init__(self, *args, **kwargs):
        self.debug = kwargs.pop('debug', False)
        logging.StreamHandler.__init__(self, *args, **kwargs)

    def emit(self, record):
        if record.exc_info:
            if isinstance(record.exc_info[1], SyntaxError):
                e = record.exc_info[1]
                record.msg = e.msg

                # Figure out where to put the carat.
                text = e.text.expandtabs()
                dedent = len(text) - len(text.lstrip())
                offset = 4 - dedent - 1 + e.offset

                record.full_stack = [(e.filename, e.lineno, '<module>',
                                      e.text + ' ' * offset + '^')]
            else:
                record.full_stack = traceback.extract_tb(record.exc_info[2])
            record.exc_info = None

        pre, stack, post = _filter_stack(record.full_stack)

        record.stack_pre = _format_stack(pre)
        record.stack = _format_stack(stack)
        record.stack_post = _format_stack(post)

        if len(stack):
            record.user_pathname = stack[-1][0]
            record.user_lineno = stack[-1][1]
        else:
            record.user_pathname = record.pathname
            record.user_lineno = record.lineno

        if len(stack) or self.debug:
            return logging.StreamHandler.emit(self, record)
        logging.root.handle(record)


def init(color='auto', debug=False, warn_once=False, stream=None):
    if color == 'always':
        colorama.init(strip=False)
    elif color == 'never':
        colorama.init(strip=True, convert=False)
    else:  # color == 'auto'
        colorama.init()

    warnings.filterwarnings('default', category=UserDeprecationWarning)
    if warn_once:
        warnings.filterwarnings('once')

    logging.addLevelName(logging.CRITICAL,
                         '\033[1;41;37m' + 'critical' + '\033[0m')
    logging.addLevelName(logging.ERROR, '\033[1;31m' + 'error' + '\033[0m')
    logging.addLevelName(logging.WARNING, '\033[1;33m' + 'warning' + '\033[0m')
    logging.addLevelName(logging.INFO, '\033[1;34m' + 'info' + '\033[0m')
    logging.addLevelName(logging.DEBUG, '\033[1;35m' + 'debug' + '\033[0m')

    logging.root.setLevel(logging.DEBUG if debug else logging.INFO)

    stackless = logging.StreamHandler(stream)
    stackless.addFilter(StackFilter(has_stack=False))

    fmt = '%(levelname)s: %(message)s'

    stackless.setFormatter(logging.Formatter(fmt))
    logging.root.addHandler(stackless)

    stackful = StackfulStreamHandler(stream, debug=debug)
    stackful.addFilter(StackFilter(has_stack=True))

    fmt = '%(levelname)s: %(user_pathname)s:%(user_lineno)d: %(message)s'
    if debug:
        fmt += '\033[2m%(stack_pre)s\033[0m'
    fmt += '%(stack)s'
    if debug:
        fmt += '\033[2m%(stack_post)s\033[0m'

    stackful.setFormatter(logging.Formatter(fmt))
    logging.root.addHandler(stackful)


def log_stack(level, message, *args, **kwargs):
    stacklevel = kwargs.pop('stacklevel', 0)
    extra = {
        'full_stack': traceback.extract_stack()[1:-1 - stacklevel],
        'show_stack': kwargs.pop('show_stack', True)
    }
    logging.log(level, message, *args, extra=extra, **kwargs)


def info(msg, show_stack=False):
    log_stack(INFO, msg, show_stack=show_stack, stacklevel=1)


def debug(msg, show_stack=True):
    log_stack(DEBUG, msg, show_stack=show_stack, stacklevel=1)


def _showwarning(message, category, filename, lineno, file=None, line=None):
    # Python 3.6 changes how stacklevel is counted.
    stacklevel = 2 if sys.version_info >= (3, 6) else 1
    log_stack(logging.WARNING, message, stacklevel=stacklevel)


warnings.showwarning = _showwarning
