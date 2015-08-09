import re
import sys
from shlex import shlex

from . import platforms
from . import iterutils

# XXX: Provide a Windows version of this function
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

_bad_posix_chars = re.compile(r'[^\w@%+=:,./-]')
_bad_windows_chars = re.compile(r'(\s|"|\\$)')
_windows_replace = re.compile(r'(\\*)("|$)')

def posix_escape(s):
    if not s:
        return '', False
    if not _bad_posix_chars.search(s):
        return s, False
    return s.replace("'", "'\"'\"'"), True

def windows_escape(s):
    if not s:
        return '', False
    if not _bad_windows_chars.search(s):
        return s, False

    def repl(m):
        quote = '\\' + m.group(2) if len(m.group(2)) else ''
        return m.group(1) * 2 + quote
    return _windows_replace.sub(repl, s), True

def posix_quote_escaped(s, escaped=True):
    return "'" + s + "'" if escaped else s

def windows_quote_escaped(s, escaped=True):
    return '"' + s + '"' if escaped else s

def posix_quote(s):
    return posix_quote_escaped(*posix_escape(s))

def windows_quote(s):
    return windows_quote_escaped(*windows_escape(s))

def posix_quote_info(s):
    s, esc = posix_escape(s)
    return posix_quote_escaped(s, esc), esc

def windows_quote_info(s):
    s, esc = windows_escape(s)
    return windows_quote_escaped(s, esc), esc

if platforms.platform_name() == 'windows':
    escape = windows_escape
    quote_escaped = windows_quote_escaped
    quote = windows_quote
    quote_info = windows_quote_info
else:
    escape = posix_escape
    quote_escaped = posix_quote_escaped
    quote = posix_quote
    quote_info = posix_quote_info
