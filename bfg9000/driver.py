import argparse
import importlib
import os
import pickle
import sys

from . import builtins
from . import find
from . import packages
from . import rules
from . import utils
from .build_inputs import BuildInputs
from .environment import Environment
from .version import __version__

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
            parser.error('{!r} does not exist'.format(path))
        if not os.path.isdir(path):
            parser.error('{!r} is not a directory'.format(path))

    args = parser.parse_args(args, namespace)

    if not args.regenerate:
        if not args.srcdir:
            parser.error('at least one of srcdir or builddir must be defined')

        if args.builddir:
            check_dir(args.srcdir, check_exist=True)
        else:
            args.builddir = '.'
            if is_srcdir(args.srcdir):
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
        args.srcdir = os.path.abspath(args.srcdir)
        args.builddir = os.path.abspath(args.builddir)
    else:
        args.srcdir, args.builddir = None, args.srcdir
        if args.srcdir:
            parser.error('source directory cannot be passed when regenerating')
        if not args.builddir:
            args.builddir = '.'

        check_dir(args.builddir, check_exist=True)
        args.builddir = os.path.abspath(args.builddir)

    return args

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('srcdir', nargs='?', help='source directory')
    parser.add_argument('builddir', nargs='?', help='build directory')
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + __version__)
    parser.add_argument('--backend', default='make', help='backend')
    parser.add_argument('--prefix', default='/usr', help='installation prefix')
    parser.add_argument('--regenerate', action='store_true',
                        help='regenerate build files')

    args = parse_args(parser)
    try:
        if args.regenerate:
            env = Environment.load(args.builddir)
        else:
            env = Environment(
                bfgpath=os.path.realpath(sys.argv[0]),
                srcdir=args.srcdir,
                builddir=args.builddir,
                backend=args.backend,
                install_prefix=os.path.abspath(args.prefix),
                variables=dict(os.environ),
            )
            env.save(args.builddir)
    except Exception as e:
        sys.stderr.write('{}: {}\n'.format(parser.prog, e))
        return 1

    build = BuildInputs()
    os.chdir(env.srcdir)
    execfile(os.path.join(env.srcdir, bfgfile), builtins.bind(build, env))

    backend = importlib.import_module('.' + env.backend, 'bfg9000.backends')
    backend.write(env, build)
