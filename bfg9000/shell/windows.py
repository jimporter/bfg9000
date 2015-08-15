import re
import sys
from array import array
from enum import Enum

from .. import iterutils

__all__ = ['split', 'listify', 'escape', 'quote_escaped', 'quote', 'quote_info']

_bad_chars = re.compile(r'(\s|"|\\$)')
_replace = re.compile(r'(\\*)("|$)')

def _tokenize(s):
    escapes = 0
    for c in s:
        if c == '\\':
            escapes += 1
        elif c == '"':
            for i in range(escapes / 2):
                yield ('char', '\\')
            yield ('char', '"') if escapes % 2 else ('quote',)
            escapes = 0
        else:
            for i in range(escapes):
                yield ('char', '\\')
            yield (('space' if c in ' \t' else 'char'), c)
            escapes = 0

def split(s):
    state = 'between'
    args = []
    buf = None

    for t in _tokenize(s):
        if state == 'between':
            if t[0] == 'char':
                buf = array('c', t[1])
                state = 'word'
            elif t[0] == 'quote':
                buf = array('c')
                state = 'quoted'
        elif state == 'word':
            if t[0] == 'quote':
                state = 'quoted'
            elif t[0] == 'char':
                buf.append(t[1])
            else: # t[0] == 'space'
                state = 'between'
                args.append(buf.tostring())
                buf = None
        else: # state == 'quoted'
            if t[0] == 'quote':
                state = 'word'
            else:
                buf.append(t[1])

    if buf is not None:
        args.append(buf.tostring())
    return args

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

    def repl(m):
        quote = '\\' + m.group(2) if len(m.group(2)) else ''
        return m.group(1) * 2 + quote
    return _replace.sub(repl, s), True

def quote_escaped(s, escaped=True):
    return '"' + s + '"' if escaped else s

def quote(s):
    return quote_escaped(*escape(s))

def quote_info(s):
    s, esc = escape(s)
    return quote_escaped(s, esc), esc
