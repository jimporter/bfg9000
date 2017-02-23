import re
import subprocess
import sys

from .arguments import parser as argparse
from .app_version import version

_class_re = re.compile(r"\[wrote (?:RegularFileObject\[|'[^']*' to )([^\]]*)")


def main():
    parser = argparse.ArgumentParser(
        prog='bfg9000-jvmoutput',
        description=('Read verbose output from a JVM compiler and write the ' +
                     'generated .class files to a file.')
    )
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + version)
    parser.add_argument('-o', type=argparse.FileType('w'), required=True,
                        dest='output', help=('the output file to list the ' +
                                             'generated .class files'))
    parser.add_argument('command', nargs=argparse.REMAINDER, metavar='COMMAND',
                        help='the command to execute')
    args = parser.parse_args()

    p = subprocess.Popen(args.command, universal_newlines=True,
                         stderr=subprocess.PIPE)
    for line in p.stderr:
        if line[0] != '[':
            sys.stdout.write(line)
            continue

        m = _class_re.match(line)
        if m:
            args.output.write(m.group(1) + '\n')
    return p.wait()
