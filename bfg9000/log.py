import logging
import os
import sys
import traceback
import warnings

logging.basicConfig(format='%(levelname)s: %(message)s')
logging.addLevelName(logging.CRITICAL, 'critical')
logging.addLevelName(logging.ERROR,    'error')
logging.addLevelName(logging.WARNING,  'warning')
logging.addLevelName(logging.INFO,     'info')
logging.addLevelName(logging.DEBUG,    'debug')

getLogger = logging.getLogger

basiclog = logging.getLogger('bfg9000')
tracelog = logging.getLogger('bfg9000.trace')
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
    # Find where the user's stack frames begin and end
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
