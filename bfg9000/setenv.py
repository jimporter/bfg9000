import argparse
import os
import subprocess
import sys

from .version import version


def main():
    parser = argparse.ArgumentParser(
        prog='bfg9000-setenv',
        usage='%(prog)s [OPTION]... [NAME=VALUE]... COMMAND [ARG]...',
        description='Set each NAME to VALUE in the environment and run ' +
                    'COMMAND.'
    )

    parser.add_argument('args', metavar='ARGS', nargs='*',
                        help='environment variable or command argument')
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + version)

    args = parser.parse_args().args
    for i, val in enumerate(args):
        name, sep, value = val.partition('=')
        if sep:
            os.environ[name] = value
        else:
            break

    if i == len(args):
        sys.stderr.write('{prog}: COMMAND is required\n'
                         .format(prog=parser.prog))
        return 1
    return subprocess.call(args[i:])
