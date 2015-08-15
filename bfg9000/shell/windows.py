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
                yield ('char', type(s)('\\'))
            yield ('char', '"') if escapes % 2 else ('quote', None)
            escapes = 0
        else:
            for i in range(escapes):
                yield ('char', type(s)('\\'))
            yield (('space' if c in ' \t' else 'char'), c)
            escapes = 0

def split(s):
    state = 'between'
    args = []

    for tok, value in _tokenize(s):
        if state == 'between':
            if tok == 'char':
                args.append(value)
                state = 'word'
            elif tok == 'quote':
                args.append('')
                state = 'quoted'
        elif state == 'word':
            if tok == 'quote':
                state = 'quoted'
            elif tok == 'char':
                args[-1] += value
            else: # t[0] == 'space'
                state = 'between'
        else: # state == 'quoted'
            if tok == 'quote':
                state = 'word'
            else:
                args[-1] += value

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
