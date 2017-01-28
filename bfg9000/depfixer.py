import sys

from enum import Enum

from .arguments import parser as argparse
from .app_version import version

# Munge the depfile so that it works a little better under Make. Specifically,
# we need all the dependencies in the depfile to also be targets, so that we
# don't get an error if a dep is removed. For a more-detailed discussion of why
# this is necessary, see <http://scottmcpeak.com/autodepend/autodepend.html>.

Token = Enum('Token', ['char', 'colon', 'space', 'newline'])
State = Enum('State', ['target', 'between_targets', 'dep', 'between_deps'])


class ParseError(ValueError):
    pass


class UnexpectedTokenError(ParseError):
    def __init__(self, tok):
        ParseError.__init__(self, "unexpected token '{}'".format(tok))


def tokenize(s):
    # The depfile syntax is a bit weird, since it seems no one quite
    # understands the correct ways to escape characters for Make in all cases
    # (made worse by the fact that even GNU Make's behavior varies across
    # versions). For our purposes though, we only need to recognize when
    # unescaped colons (always followed by whitespace in the depfile
    # generators) and unescaped spaces are emitted.

    s = iter(s)
    while True:
        c = next(s, None)
        if c is None:
            return

        if c == ':':
            c = next(s)
            if c in ' \t\n':
                yield (Token.colon, None)
                if c == '\n':
                    yield (Token.newline, None)
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
            if tok == Token.space:
                state = State.between_targets
            elif tok == Token.colon:
                state = State.between_deps
            elif tok != Token.char:
                raise UnexpectedTokenError(tok)
        elif state == State.between_targets:
            if tok == Token.char:
                state = State.target
            elif tok == Token.colon:
                state = State.between_deps
            elif tok != Token.space:
                raise UnexpectedTokenError(tok)
        elif state == State.dep:
            if tok == Token.char:
                outstream.write(value)
            elif tok == Token.space:
                outstream.write(':\n')
                state = State.between_deps
            elif tok == Token.newline:
                outstream.write(':\n')
                state = State.target
            else:
                raise UnexpectedTokenError(tok)
        else:  # state == State.between_deps
            if tok == Token.char:
                state = State.dep
                outstream.write(value)
            elif tok == Token.newline:
                state = State.target
            elif tok != Token.space:
                raise UnexpectedTokenError(tok)

    if state != State.target:
        raise ParseError('unexpected end of file')


def main():
    parser = argparse.ArgumentParser(
        prog='bfg9000-depfixer',
        description='Read in a depfile (in Makefile syntax) on stdin and ' +
                    'output all the dependencies as targets on stdout.'
    )
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + version)
    parser.parse_args()

    try:
        emit_deps(sys.stdin, sys.stdout)
    except Exception as e:
        parser.error(e)
