import re
import sys

from .arguments import parser as argparse
from .version import version


def main():
    parser = argparse.ArgumentParser(
        prog='bfg9000-jvmoutput',
        description='Read verbose output from a JVM compiler on stdin and ' +
                    'print the generated .class files on stdout.'
    )
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + version)
    parser.parse_args()

    for i in sys.stdin:
        m = re.match(r"\[wrote (?:RegularFileObject\[|'[^']*' to )([^\]]*)", i)
        if m:
            sys.stdout.write(m.group(1) + '\n')
