import itertools
import re
from shlex import shlex
from six import iteritems, string_types

from .. import iterutils
from .list import shell_list
from ..platforms.host import platform_info
from ..safe_str import jbos, safe_str, shell_literal

__all__ = ['split', 'join', 'listify', 'inner_quote', 'inner_quote_info',
           'wrap_quotes', 'quote', 'quote_info', 'escape_line', 'join_lines',
           'local_env', 'global_env']

_bad_chars = re.compile(r'[^\w@%+=:,./-]')
_ends_unescaped_quote = re.compile(r"(^|[^\\])(\\\\)*'$")


def split(s, type=list, escapes=False):
    if not isinstance(s, string_types):
        raise TypeError('expected a string')
    lexer = shlex(s, posix=True)
    lexer.commenters = ''
    if not escapes:
        lexer.escape = ''
    lexer.whitespace_split = True
    return type(lexer)


def join(args):
    return ' '.join(quote(i) for i in args)


def listify(thing, type=list):
    if isinstance(thing, string_types):
        return split(thing, type)
    return iterutils.listify(thing, type=type)


def inner_quote_info(s):
    if _bad_chars.search(s):
        return s.replace("'", r"'\''"), True
    return s, False


def inner_quote(s):
    return inner_quote_info(s)[0]


def wrap_quotes(s):
    def q(has_quote):
        return '' if has_quote else "'"

    # Any string less than 3 characters long can't have escaped quotes.
    if len(s) < 3:
        return "'" + s + "'"

    start = 1 if s[0] == "'" else None
    # Thanks to `inner_quote_info` above, we can guarantee that any single-
    # quotes are unescaped, so we can deduplicate them if they're at the end.
    end = -1 if s[-1] == "'" else None
    return q(start) + s[start:end] + q(end)


def quote_info(s):
    s, quoted = inner_quote_info(s)
    return (wrap_quotes(s), True) if quoted else (s, False)


def quote(s):
    return quote_info(s)[0]


def _escape_word(word):
    # Since we can sometimes use an sh-style shell even on Windows (e.g.
    # with the Make backend), we want to escape backslashes when writing an
    # already "escaped" command line. Otherwise, Windows users would be
    # pretty surprised to find that all the paths they specified like
    # C:\foo\bar are broken!
    if platform_info().family == 'windows':
        word = word.replace('\\', '\\\\')
    return shell_literal(word)


def escape_line(line, listify=False):
    if iterutils.isiterable(line):
        return iterutils.listify(line) if listify else line

    line = safe_str(line)
    if isinstance(line, string_types):
        line = _escape_word(line)
    elif isinstance(line, jbos):
        line = jbos(*(_escape_word(i) if isinstance(i, string_types) else i
                      for i in line.bits))
    return shell_list([line])


def join_lines(lines):
    result = []
    for i in iterutils.tween( (escape_line(j, listify=True) for j in lines),
                              shell_list([shell_literal('&&')]) ):
        result += i
    return result


def local_env(env, line):
    if env:
        eq = shell_literal('=')
        env_vars = shell_list(jbos(safe_str(name), eq, safe_str(value))
                              for name, value in iteritems(env))
    else:
        env_vars = []
    return env_vars + escape_line(line, listify=True)


def global_env(env, lines=None):
    eq = shell_literal('=')
    env_vars = (shell_list([
        'export', jbos(safe_str(name), eq, safe_str(value))
    ]) for name, value in iteritems(env))
    return join_lines(itertools.chain(env_vars, lines or []))
