import argparse
import os

from .find import FindCache
from .version import __version__

def scan():
    from os.path import getmtime

    parser = argparse.ArgumentParser()
    parser.add_argument('path', nargs='?', default=FindCache.cachefile,
                        help='path to the cache file (default: %(default)s)')
    parser.add_argument('-S', '--skip-if-newer', metavar='FILE',
                        help='return immediately if FILE is newer than the ' +
                             'cache file')
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + __version__)

    args = parser.parse_args()
    if args.skip_if_newer:
        if os.path.getmtime(args.skip_if_newer) > os.path.getmtime(args.path):
            return

    if FindCache.dirty(args.path):
        os.utime(args.path, None)
