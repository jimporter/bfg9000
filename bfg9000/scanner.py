import argparse
import os

from . import find
from .version import __version__

def scan():
    from os.path import getmtime

    parser = argparse.ArgumentParser()
    parser.add_argument('path', nargs='?', default=find.cachefile)
    parser.add_argument('-S', '--skip-if-newer')
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + __version__)

    args = parser.parse_args()
    if args.skip_if_newer:
        if os.path.getmtime(args.skip_if_newer) > os.path.getmtime(args.path):
            return

    if find.FindCache.load(args.path).has_changes():
        os.utime(args.path, None)
