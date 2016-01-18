import argparse
import sys

from enum import Enum

from .version import version

Token = Enum('Token', ['char', 'colon', 'space', 'newline'])
State = Enum('State', ['target', 'between', 'dep', 'end'])

# Munge the depfile so that it works a little better under Make. Specifically,
# we need all the dependencies in the depfile to also be targets, so that we
# don't get an error if a dep is removed. For a more-detailed discussion of why
# this is necessary, see <http://scottmcpeak.com/autodepend/autodepend.html>.


def tokenize(s):
    # The depfile syntax is a bit weird, since it seems no one quite
    # understands the correct ways to escape characters for Make in all cases
    # (made worse by the fact that even GNU Make's behavior varies across
    # versions). For our purposes though, we only need to recognize when
    # unescaped colons (always followed by spaces in the depfile generators)
    # and unescaped spaces are emitted.

    s = iter(s)
    while True:
        c = next(s, None)
        if c is None:
            return

        if c == ':':
            c = next(s)
            if c == ' ':
                yield (Token.colon, None)
                continue
            else:
                yield (Token.char, ':')

        if c == '\\':
            c = next(s)
            if c != '\n':  # Swallow escaped newlines.
                yield (Token.char, '\\')
                yield (Token.char, c)
        elif c in ' \t':
            yield (Token.space, None)
        elif c == '\n':
            yield (Token.newline, None)
        else:
            yield (Token.char, c)


def emit_deps(instream, outstream):
    state = State.target

    for tok, value in tokenize(instream.read()):
        if state == State.target:
            if tok == Token.colon:
                state = State.between
            elif tok != Token.char:
                raise Exception(tok)
        elif state == State.dep:
            if tok == Token.char:
                outstream.write(value)
            elif tok == Token.space:
                outstream.write(':\n')
                state = State.between
            elif tok == Token.newline:
                outstream.write(':\n')
                state = State.end
            else:
                raise Exception(tok)
        elif state == State.between:
            if tok == Token.char:
                state = State.dep
                outstream.write(value)
            elif tok == Token.newline:
                state = State.end
            elif tok != Token.space:
                raise Exception(tok)
        else:  # state == State.end
            if tok != Token.newline:
                raise Exception(tok)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + version)
    parser.parse_args()

    emit_deps(sys.stdin, sys.stdout)
