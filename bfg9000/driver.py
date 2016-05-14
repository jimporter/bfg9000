import argparse
import os
import re
import sys

from . import builtins
from . import log
from .backends import get_backends
from .build_inputs import BuildInputs
from .environment import Environment, EnvVersionError
from .path import InstallRoot, Path, Root, samefile
from .platforms import platform_info
from .version import version

bfgfile = 'build.bfg'
logger = log.getLogger(__name__)

description = """
bfg9000 ("build file generator") is a cross-platform build configuration system
with an emphasis on making it easy to define how to build your software. It
converts a Python-based build script into the appropriate files for your
underlying build system of choice.
"""


def is_srcdir(path):
    return os.path.exists(os.path.join(path, bfgfile))


def parse_args(parser, args=None, namespace=None):
    def check_dir(path):
        if not os.path.exists(path):
            parser.error("'{}' does not exist".format(path))
        if not os.path.isdir(path):
            parser.error("'{}' is not a directory".format(path))

    args = parser.parse_args(args, namespace)

    if args.subcommand == 'build':
        if not args.srcdir:
            parser.error('at least one of srcdir or builddir must be defined')

        if args.builddir:
            check_dir(args.srcdir)
        else:
            args.builddir = '.'
            if not is_srcdir(args.srcdir):
                args.srcdir, args.builddir = args.builddir, args.srcdir

        if os.path.exists(args.builddir):
            check_dir(args.builddir)
            if samefile(args.srcdir, args.builddir):
                parser.error('source and build directories must be different')

        if not is_srcdir(args.srcdir):
            parser.error('source directory must contain a build.bfg file')
        if is_srcdir(args.builddir):
            parser.error('build directory must not contain a build.bfg file')

        if not os.path.exists(args.builddir):
            os.mkdir(args.builddir)
        args.srcdir = Path(os.path.abspath(args.srcdir))
        args.builddir = Path(os.path.abspath(args.builddir))
    else:
        check_dir(args.builddir)
        args.builddir = Path(os.path.abspath(args.builddir))

    return args


def execute_script(env, filename=bfgfile):
    bfgpath = Path(filename, Root.srcdir)
    build = BuildInputs(env, bfgpath)
    builtin_dict = builtins.bind(build_inputs=build, env=env)

    with open(bfgpath.string(env.path_roots), 'r') as f:
        os.chdir(env.srcdir.string())
        code = compile(f.read(), filename, 'exec')
        try:
            exec(code, builtin_dict)
        except SystemExit:
            pass
        except Exception as e:
            log.exception(e)
            raise SystemExit(1)

    return build


def main():
    backends = get_backends()
    install_dirs = platform_info().install_dirs
    path_help = 'installation path for {} (default: %(default)r)'

    def path_arg(value):
        return Path(os.path.abspath(value))

    parser = argparse.ArgumentParser(prog='bfg9000', description=description)
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + version)
    parser.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('-c', '--color', nargs='?', metavar='WHEN',
                        choices=['always', 'never', 'auto'],
                        default='auto', const='always',
                        help=('show colored output (one of: %(choices)s; ' +
                              'default: %(default)s)'))

    subparsers = parser.add_subparsers(dest='subcommand')

    buildp = subparsers.add_parser('build')
    buildp.add_argument('srcdir', nargs='?', help='source directory')
    buildp.add_argument('builddir', nargs='?', help='build directory')
    buildp.add_argument('--backend', metavar='BACKEND',
                        choices=list(backends.keys()),
                        default=list(backends.keys())[0],
                        help=('build backend (one of %(choices)s; default: ' +
                              '%(default)s)'))
    buildp.add_argument('--prefix', type=path_arg, metavar='PATH',
                        default=install_dirs[InstallRoot.prefix],
                        help='installation prefix (default: %(default)r)')
    buildp.add_argument('--bindir', type=path_arg, metavar='PATH',
                        default=install_dirs[InstallRoot.bindir],
                        help=path_help.format('executables'))
    buildp.add_argument('--libdir', type=path_arg, metavar='PATH',
                        default=install_dirs[InstallRoot.libdir],
                        help=path_help.format('libraries'))
    buildp.add_argument('--includedir', type=path_arg, metavar='PATH',
                        default=install_dirs[InstallRoot.includedir],
                        help=path_help.format('headers'))

    regenp = subparsers.add_parser('regenerate')
    regenp.add_argument('builddir', nargs='?', default='.',
                        help='build directory')

    args = parse_args(parser)
    log.init(args.color, debug=args.debug)

    if args.subcommand == 'regenerate':
        try:
            env = Environment.load(args.builddir.string())
        except Exception as e:
            msg = 'Unable to reload environment'
            if str(e):
                msg += ': {}'.format(str(e))
            if isinstance(e, EnvVersionError):
                msg += '\n  Please re-run bfg9000 manually'
            logger.error(msg)
            return 1
    else:
        # De-munge the entry point if we're on Windows.
        bfgpath = Path(os.path.realpath(
            re.sub('-script.py$', '.exe', sys.argv[0])
        ))
        env = Environment(
            bfgpath=bfgpath,
            backend=args.backend,
            backend_version=backends[args.backend].version(),
            srcdir=args.srcdir,
            builddir=args.builddir,
            install_dirs={
                InstallRoot.prefix: args.prefix,
                InstallRoot.bindir: args.bindir,
                InstallRoot.libdir: args.libdir,
                InstallRoot.includedir: args.includedir,
            }
        )
        env.save(args.builddir.string())

    build = execute_script(env)
    backends[env.backend].write(env, build)
