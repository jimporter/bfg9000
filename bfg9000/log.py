import colorama
import logging
import os
import sys
import traceback
import warnings

getLogger = logging.getLogger

basiclog = logging.getLogger('bfg9000')
tracelog = logging.getLogger('bfg9000.trace')


def init(color='auto', debug=False):
    if color == 'always':
        colorama.init(strip=False)
    elif color == 'never':
        colorama.init(strip=True, convert=False)
    else:  # color == 'auto'
        colorama.init()

    logging.basicConfig(format='%(levelname)s: %(message)s',
                        level=logging.DEBUG if debug else logging.WARNING)

    logging.addLevelName(logging.CRITICAL,
                         '\033[1;41;37m' + 'critical' + '\033[0m')
    logging.addLevelName(logging.ERROR, '\033[1;31m' + 'error' + '\033[0m')
    logging.addLevelName(logging.WARNING, '\033[1;33m' + 'warning' + '\033[0m')
    logging.addLevelName(logging.INFO, '\033[1;34m' + 'info' + '\033[0m')
    logging.addLevelName(logging.DEBUG, '\033[1;35m' + 'debug' + '\033[0m')

    tracelog.propagate = False
    console = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)s: %(file)s:%(line)d: ' +
                                  '%(message)s\n%(traceback)s')
    console.setFormatter(formatter)
    tracelog.addHandler(console)


def _showwarning(message, category, filename, lineno, file=None, line=None):
    stack = traceback.extract_stack()[1:]
    _log_trace(logging.WARN, message, stack)

warnings.showwarning = _showwarning
warnings.filterwarnings('once')


def _is_bfg_src(filename):
    rel = os.path.relpath(filename, os.path.dirname(__file__))
    return not rel.startswith(os.pardir + os.sep)


def _log_trace(lvl, msg, summary):
    if tracelog.getEffectiveLevel() > logging.DEBUG:
        # Find where the user's stack frames begin and end.
        gen = enumerate(summary)
        for start, line in gen:
            if not _is_bfg_src(line[0]):
                break
        else:
            start = len(summary)

        for end, line in gen:
            if _is_bfg_src(line[0]):
                break
        else:
            end = len(summary)

        summary = summary[start:end]

    if len(summary):
        tracelog.log(lvl, msg, extra={
            'file': summary[-1][0], 'line': summary[-1][1],
            'traceback': ''.join(traceback.format_list(summary)).rstrip()
        })
    else:
        basiclog.log(lvl, msg)


def exception(e):
    tb = traceback.extract_tb(sys.exc_info()[2])
    _log_trace(logging.ERROR, e, tb)
