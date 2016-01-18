import argparse
import errno
import os
import sys

from .version import version


def makedirs(path, mode=0o777, exist_ok=False):
    try:
        os.makedirs(path)
    except OSError as e:
        if not exist_ok or e.errno != errno.EEXIST or not os.path.isdir(path):
            raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='directory to create')
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + version)
    args = parser.parse_args()

    try:
        makedirs(args.path, exist_ok=True)
        return 0
    except Exception as e:
        sys.stderr.write('{prog}: error creating directories: {msg}\n'
                         .format(prog=parser.prog, msg=e))
        return 1
