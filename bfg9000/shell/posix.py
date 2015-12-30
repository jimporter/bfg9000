import re
from shlex import shlex
from six import iteritems, string_types

from .. import iterutils
from ..safe_str import escaped_str, jbos, safe_str

__all__ = ['split', 'listify', 'escape', 'quote_escaped', 'quote',
           'quote_info', 'join_commands', 'local_env', 'global_env']

_bad_chars = re.compile(r'[^\w@%+:,./-]')


def split(s):
    if not isinstance(s, string_types):
        raise TypeError('expected a string')
    lexer = shlex(s, posix=True)
    lexer.commenters = ''
    lexer.whitespace_split = True
    return list(lexer)


def listify(thing):
    if thing is None:
        return []
    elif iterutils.isiterable(thing):
        return list(thing)
    else:
        return split(thing)


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


def join_commands(commands):
    return iterutils.tween(commands, escaped_str(' && '))


def local_env(env):
    eq = escaped_str('=')
    return [ jbos(safe_str(name), eq, safe_str(value))
             for name, value in iteritems(env) ]


def global_env(env):
    eq = escaped_str('=')
    return [ ['export', jbos(safe_str(name), eq, safe_str(value))]
             for name, value in iteritems(env) ]
