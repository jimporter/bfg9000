from __future__ import division

import re
from enum import Enum
from six import iteritems

from .. import iterutils
from ..safe_str import escaped_str, safe_str

__all__ = ['split', 'listify', 'escape', 'quote_escaped', 'quote',
           'quote_info', 'join_commands', 'global_env']

# XXX: We need a way to escape cmd.exe-specific characters.
_bad_chars = re.compile(r'(\s|"|\\$)')
_replace = re.compile(r'(\\*)("|$)')

_Token = Enum('Token', ['char', 'quote', 'space'])
_State = Enum('State', ['between', 'char', 'word', 'quoted'])


def _tokenize(s):
    escapes = 0
    for c in s:
        if c == '\\':
            escapes += 1
        elif c == '"':
            for i in range(escapes // 2):
                yield (_Token.char, type(s)('\\'))
            yield (_Token.char, '"') if escapes % 2 else (_Token.quote, None)
            escapes = 0
        else:
            for i in range(escapes):
                yield (_Token.char, type(s)('\\'))
            yield ((_Token.space if c in ' \t' else _Token.char), c)
            escapes = 0


def split(s):
    state = _State.between
    args = []

    for tok, value in _tokenize(s):
        if state == _State.between:
            if tok == _Token.char:
                args.append(value)
                state = _State.word
            elif tok == _Token.quote:
                args.append('')
                state = _State.quoted
        elif state == _State.word:
            if tok == _Token.quote:
                state = _State.quoted
            elif tok == _Token.char:
                args[-1] += value
            else:  # tok == _Token.space
                state = _State.between
        else:  # state == _State.quoted
            if tok == _Token.quote:
                state = _State.word
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


def join_commands(commands):
    return iterutils.tween(commands, escaped_str(' && '))


def global_env(env):
    # Join the name and value so they get quoted together, if necessary.
    return [ ['set', safe_str(name) + '=' + safe_str(value)]
             for name, value in iteritems(env) ]
