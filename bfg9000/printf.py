import sys

from .arguments import parser as argparse
from .app_version import version


def escaped_str(s):
    return s.encode().decode('unicode-escape')


def main():
    parser = argparse.ArgumentParser(
        prog='bfg9000-printf',
        description='Print ARGS according to FORMAT.'
    )

    parser.add_argument('format', metavar='FORMAT', type=escaped_str,
                        help='controls the output as in C printf')
    parser.add_argument('args', metavar='ARGS', nargs='*',
                        help='arguments to print according to FORMAT')
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + version)

    args = parser.parse_args()

    # XXX: This only supports format strings with one format spec.
    for i in args.args:
        sys.stdout.write(args.format % i)
