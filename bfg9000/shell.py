import platforms
import re
import sys
from shlex import shlex

def split(s):
    if not isinstance(s, basestring):
        raise TypeError('expected a string')
    lexer = shlex(s, posix=True)
    lexer.commenters = ''
    lexer.whitespace_split = True
    return list(lexer)

_bad_chars = re.compile(r'[^\w@%+=:,./-]')

def quote_posix(s):
    if not s:
        return "''"
    if _bad_chars.search(s) is None:
        return s
    return "'" + s.replace("'", "'\"'\"'") + "'"

def quote_windows(s):
    # TODO: Implement this!
    return s

if platforms.platform_name() == 'windows':
    quote = quote_windows
else:
    quote = quote_posix
