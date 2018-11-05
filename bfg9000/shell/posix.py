import itertools
import re
from shlex import shlex
from six import iteritems, string_types

from .. import iterutils
from .list import shell_list
from ..platforms import platform_name
from ..safe_str import jbos, safe_str, shell_literal

__all__ = ['split', 'join', 'listify', 'escape', 'quote_escaped', 'quote',
           'quote_info', 'escape_line', 'join_lines', 'local_env',
           'global_env']

_bad_chars = re.compile(r'[^\w@%+:,./-]')


def split(s, type=list):
    if not isinstance(s, string_types):
        raise TypeError('expected a string')
    lexer = shlex(s, posix=True)
    lexer.commenters = ''
    lexer.escape = ''
    lexer.whitespace_split = True
    return type(lexer)


def join(args):
    return ' '.join(quote(i) for i in args)


def listify(thing, type=list):
    if isinstance(thing, string_types):
        return split(thing, type)
    return iterutils.listify(thing, type=type)


def escape(s):
    if not s:
        return '', False
    if not _bad_chars.search(s):
        return s, False
    return s.replace("'", "'\"'\"'"), True


def quote_escaped(s, escaped=True):
    return "'" + s + "'" if escaped else s


def quote(s):
    return quote_escaped(*escape(s))


def quote_info(s):
    s, esc = escape(s)
    return quote_escaped(s, esc), esc


def escape_line(line, listify=False):
    if iterutils.isiterable(line):
        return iterutils.listify(line) if listify else line

    line = safe_str(line)
    if isinstance(line, string_types):
        # Since we can sometimes use an sh-style shell even on Windows (e.g.
        # with the Make backend), we want to escape backslashes when writing an
        # already "escaped" command line. Otherwise, Windows users would be
        # pretty surprised to find that all the paths they specified like
        # C:\foo\bar are broken!
        if platform_name() in ('winnt', 'win9x', 'msdos'):
            line = line.replace('\\', '\\\\')
        line = shell_literal(line)
    return shell_list([line])


def join_lines(lines):
    result = []
    for i in iterutils.tween( (escape_line(j, listify=True) for j in lines),
                              shell_list([shell_literal('&&')]) ):
        if i:
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
