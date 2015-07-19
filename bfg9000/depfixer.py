import argparse
import shlex
import sys

from .backends.make.syntax import MakeWriter
from .version import __version__

def main():
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
        out.write(i, 'target')
        out.write_literal(':\n')
