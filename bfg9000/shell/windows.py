from __future__ import division

import itertools
import re
from collections import MutableSequence
from enum import Enum
from six import iteritems, string_types

from .list import shell_list
from .. import iterutils
from ..safe_str import safe_str, shell_literal

__all__ = ['split', 'join', 'listify', 'escape', 'quote_escaped', 'quote',
           'quote_info', 'escape_line', 'join_lines', 'global_env']

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


def split(s, type=list):
    if not isinstance(s, string_types):
        raise TypeError('expected a string')

    mutable = isinstance(type, MutableSequence)
    state = _State.between
    args = (type if mutable else list)()

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

    return args if mutable else type(args)


def join(args):
    return ' '.join(quote(i) for i in args)


def listify(thing, type=list):
    if isinstance(thing, string_types):
        return split(thing, type)
    return iterutils.listify(thing, type=type)


def escape(s, escape_percent=False):
    if not s:
        return '', False

    # In some contexts (mainly certain uses of the Windows shell), we want to
    # escape percent signs. This doesn't count as "escaping" for the purposes
    # of quoting the result though.
    if escape_percent:
        s = s.replace('%', '%%')

    if not _bad_chars.search(s):
        return s, False

    def repl(m):
        quote = '\\' + m.group(2) if len(m.group(2)) else ''
        return m.group(1) * 2 + quote
    return _replace.sub(repl, s), True


def quote_escaped(s, escaped=True):
    return '"' + s + '"' if escaped else s


def quote(s, escape_percent=False):
    return quote_escaped(*escape(s, escape_percent))


def quote_info(s, escape_percent=False):
    s, esc = escape(s, escape_percent)
    return quote_escaped(s, esc), esc


def escape_line(line, listify=False):
    if iterutils.isiterable(line):
        return iterutils.listify(line) if listify else line

    line = safe_str(line)
    if isinstance(line, string_types):
        line = shell_literal(line)
    return shell_list([line])


def join_lines(lines):
    result = []
    for i in iterutils.tween( (escape_line(j, listify=True) for j in lines),
                              shell_list([shell_literal('&&')]) ):
        if i:
            result += i
    return result


def global_env(env, lines=[]):
    # Join the name and value so they get quoted together, if necessary.
    env_vars = (shell_list(['set', safe_str(name) + '=' + safe_str(value)])
                for name, value in iteritems(env))
    return join_lines(itertools.chain(env_vars, lines))
