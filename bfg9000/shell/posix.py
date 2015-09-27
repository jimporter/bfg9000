import re
from shlex import shlex

from .. import iterutils
from .. import safe_str

__all__ = ['split', 'listify', 'escape', 'quote_escaped', 'quote', 'quote_info',
           'env_var']

_bad_chars = re.compile(r'[^\w@%+:,./-]')

def split(s):
    if not isinstance(s, basestring):
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

def env_var(name, value):
    return safe_str.jbos(name, safe_str.escaped_str('='), value)
