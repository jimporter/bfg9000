import argparse
import sys

from .pathutils import makedirs
from .version import version


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
