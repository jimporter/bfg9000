import errno
import os
import re
import subprocess
import sys

from .arguments import parser as argparse
from .app_version import version

# This captures a few kinds of messages emitted via `javac -verbose` (or
# scalac or whatever):
#   JDK 1-8:  [wrote RegularFileObject[path]]
#   JDK 9-10: [wrote DirectoryFileObject[bad:path]]
#   JDK 11+:  [wrote path]
#   Scala:    [wrote 'thing' to path]
_class_re = re.compile(
    r"\[wrote ((?:Regular|Directory)FileObject\[|'[^']*' to |)([^\]]*)"
)


def main():
    parser = argparse.ArgumentParser(
        prog='bfg9000-jvmoutput',
        description=('Read verbose output from a JVM compiler and write the ' +
                     'generated .class files to a file.')
    )
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + version)
    parser.add_argument('-o', type=argparse.FileType('w'), default=sys.stdout,
                        dest='output', help=('the output file to list the ' +
                                             'generated .class files'))
    parser.add_argument('command', nargs=argparse.REMAINDER, metavar='COMMAND',
                        help='the command to execute')
    args = parser.parse_args()

    if len(args.command) == 0:
        parser.error('command required')

    try:
        p = subprocess.Popen(args.command, universal_newlines=True,
                             stderr=subprocess.PIPE)
    except OSError as e:
        if e.errno == errno.ENOENT:
            parser.exit(66, 'command not found: {}\n'.format(args.command[0]))
        raise  # pragma: no cover

    for line in p.stderr:
        if line[0] != '[':
            sys.stderr.write(line)
            continue

        m = _class_re.match(line)
        if m:
            kind = m.group(1)
            class_file = m.group(2)
            # JDK 9-10 emits broken paths; fix them. For more info, see
            # <https://bugs.openjdk.java.net/browse/JDK-8194893>.
            if kind == 'DirectoryFileObject[':
                class_file = class_file.replace(':', os.path.sep)
            args.output.write(class_file + '\n')
    return p.wait()
