import subprocess

from .app_version import version
from .arguments import parser as argparse
from .iterutils import tween


def make_depfile(subcmd, output, depfile):
    deps = subprocess.check_output(subcmd + ['--list'],
                                   universal_newlines=True)
    deps = deps.strip().split('\n')

    with open(depfile, 'w') as f:
        f.write(output + ': ')
        for i in tween(deps, ' \\\n'):
            f.write(i)
        f.write('\n')


def run_rcc(subcmd, output):
    return subprocess.call(subcmd + ['-o', output])


def main():
    parser = argparse.ArgumentParser(
        prog='bfg9000-rccdep',
        usage='%(prog)s SUBCMD -o FILE -d FILE',
        description="Write a depfile (in Makefile syntax) for Qt's rcc " +
                    "tool, and then run rcc."
    )
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + version)
    parser.add_argument('-o', '--output', required=True, metavar='FILE',
                        help='the output file for rcc (required)')
    parser.add_argument('-d', '--depfile', required=True, metavar='FILE',
                        help='the depfile to generate (required)')
    args, subcommand = parser.parse_known_args()

    subparser = argparse.ArgumentParser(prog=parser.prog, usage=parser.usage)
    subparser.add_argument('command', nargs='+')
    subargs = subparser.parse_known_args(subcommand)[0]

    try:
        make_depfile(subargs.command, args.output, args.depfile)
        return run_rcc(subcommand, args.output)
    except Exception as e:
        parser.error(e)
