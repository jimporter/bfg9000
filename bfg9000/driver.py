import argparse
import os
import re
import sys

from . import builtins
from .backends import get_backends
from .build_inputs import BuildInputs
from .environment import Environment, EnvVersionError
from .path import Path, InstallRoot
from .platforms import platform_info
from .version import version

bfgfile = 'build.bfg'


def is_srcdir(path):
    return os.path.exists(os.path.join(path, bfgfile))


def samefile(path1, path2):
    if hasattr(os.path, 'samefile'):
        return os.path.samefile(path1, path2)
    else:
        # This isn't entirely accurate, but it's close enough, and should only
        # be necessary for Windows with Python 2.x.
        return os.path.realpath(path1) == os.path.realpath(path2)


def parse_args(parser, args=None, namespace=None):
    def check_dir(path, check_exist=False):
        if not os.path.exists(path):
            parser.error("'{}' does not exist".format(path))
        if not os.path.isdir(path):
            parser.error("'{}' is not a directory".format(path))

    args = parser.parse_args(args, namespace)

    if not args.regenerate:
        if not args.srcdir:
            parser.error('at least one of srcdir or builddir must be defined')

        if args.builddir:
            check_dir(args.srcdir, check_exist=True)
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
        args.srcdir, args.builddir = None, args.srcdir
        if args.srcdir:
            parser.error('source directory cannot be passed when regenerating')
        if not args.builddir:
            args.builddir = '.'

        check_dir(args.builddir, check_exist=True)
        args.builddir = Path(os.path.abspath(args.builddir))

    return args


def execute_script(env, filename=bfgfile):
    builtins.load()
    build = BuildInputs()
    builtin_dict = builtins.bind(build_inputs=build, env=env)

    bfgpath = env.srcdir.append(filename).string()
    with open(bfgpath, 'r') as f:
        os.chdir(env.srcdir.string())
        code = compile(f.read(), filename, 'exec')
        try:
            exec(code, builtin_dict, {})
        except SystemExit:
            pass

    return build


def main():
    backends = get_backends()
    install_dirs = platform_info().install_dirs
    path_help = 'installation path for {} (default: %(default)r)'

    def path_arg(value):
        return Path(os.path.abspath(value))

    parser = argparse.ArgumentParser(prog='bfg9000')
    parser.add_argument('srcdir', nargs='?', help='source directory')
    parser.add_argument('builddir', nargs='?', help='build directory')
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + version)
    parser.add_argument('--backend', choices=list(backends.keys()),
                        default=list(backends.keys())[0],
                        help='backend (default: %(default)s)')
    parser.add_argument('--prefix', type=path_arg, metavar='PATH',
                        default=install_dirs[InstallRoot.prefix],
                        help='installation prefix (default: %(default)r)')
    parser.add_argument('--bindir', type=path_arg, metavar='PATH',
                        default=install_dirs[InstallRoot.bindir],
                        help=path_help.format('executables'))
    parser.add_argument('--libdir', type=path_arg, metavar='PATH',
                        default=install_dirs[InstallRoot.libdir],
                        help=path_help.format('libraries'))
    parser.add_argument('--includedir', type=path_arg, metavar='PATH',
                        default=install_dirs[InstallRoot.includedir],
                        help=path_help.format('headers'))
    parser.add_argument('--regenerate', action='store_true',
                        help='regenerate build files')

    args = parse_args(parser)
    if args.regenerate:
        try:
            env = Environment.load(args.builddir.string())
        except Exception as e:
            sys.stderr.write('{prog}: error loading environment: {msg}\n'
                             .format(prog=parser.prog, msg=e))
            if isinstance(e, EnvVersionError):
                sys.stderr.write('Please re-run bfg9000 manually.\n')
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
