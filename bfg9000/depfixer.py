import argparse
import shlex
import sys

from .backends.make.syntax import MakeWriter, Syntax
from .version import __version__

def main():
    # Munge the depfile so that it works a little better under Make.
    # Specifically, we need all the dependencies in the depfile to also be
    # targets, so that we don't get an error if a dep is removed. See
    # <http://scottmcpeak.com/autodepend/autodepend.html> for a discussion of
    # how this works.

    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + __version__)
    parser.parse_args()

    lexer = shlex.shlex(sys.stdin, posix=True)
    lexer.whitespace_split = True

    dep = lexer.get_token()
    if not dep.endswith(':'):
        sys.stderr.write('invalid depfile')
        return 1

    files = []
    while True:
        tok = lexer.get_token()
        if tok == lexer.eof:
            break
        if not tok.isspace():
            files.append(tok)

    out = MakeWriter(sys.stdout)
    for i in files:
        out.write(i, Syntax.target)
        out.write_literal(':\n')
