import re
import sys
from shlex import shlex

from . import platforms
from . import utils

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
    elif utils.isiterable(thing):
        return list(thing)
    else:
        return split(thing)

_bad_posix_chars = re.compile(r'[^\w@%+=:,./-]')
_bad_windows_chars = re.compile(r'(\s|"|\\$)')
_windows_replace = re.compile(r'(\\*)("|$)')

def quote_posix(s):
    if not s:
        return "''"
    if not _bad_posix_chars.search(s):
        return s
    return "'" + s.replace("'", "'\"'\"'") + "'"

def quote_windows(s):
    if not s:
        return '""'
    if not _bad_windows_chars.search(s):
        return s

    def repl(m):
        quote = '\\' + m.group(2) if len(m.group(2)) else ''
        return m.group(1) * 2 + quote
    return '"' + _windows_replace.sub(repl, s) + '"'

if platforms.platform_name() == 'windows':
    quote = quote_windows
else:
    quote = quote_posix
