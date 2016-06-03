import argparse
import os
import re
import sys

from . import builtins
from . import log
from .backends import list_backends
from .build_inputs import BuildInputs
from .environment import Environment, EnvVersionError
from .path import abspath, InstallRoot, Path, Root, samefile
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

build_desc = """
Generate the necessary build files to perform actual builds. If DIRECTORY is a
source directory (i.e. it contains a build.bfg file), the build files will be
created in the current directory. Otherwise, DIRECTORY is treated as the build
directory, and bfg9000 will look for a build.bfg file in the current directory.
"""

buildex_desc = """
Generate the necessary build files to perform actual builds from a build.bfg
file in SRCDIR, and place them in BUILDDIR.
"""

regenerate_desc = """
Regenerate an existing set of build files needed to perform actual builds. This
is typically run automatically if bfg9000 determines that the build files are
out of date.
"""


def is_srcdir(path):
    return os.path.exists(os.path.join(path, bfgfile))


def check_dir(parser, pathstr, must_exist=True):
    if os.path.exists(pathstr):
        if not os.path.isdir(pathstr):
            parser.error("'{}' is not a directory".format(pathstr))
    elif must_exist:
        parser.error("'{}' does not exist".format(pathstr))


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


class Directory(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        check_dir(parser, values, must_exist=False)
        setattr(namespace, self.dest, abspath(values))


class ExistingDirectory(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        check_dir(parser, values)
        setattr(namespace, self.dest, abspath(values))


class DirectoryPair(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        cwd = '.'

        check_dir(parser, values)

        if is_srcdir(values):
            srcdir, builddir = values, cwd
        else:
            srcdir, builddir = cwd, values

        namespace.srcdir = abspath(srcdir)
        namespace.builddir = abspath(builddir)


def add_generic_args(parser):
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + version)
    parser.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('-c', '--color', nargs='?', metavar='WHEN',
                        choices=['always', 'never', 'auto'],
                        default='auto', const='always',
                        help=('show colored output (one of: %(choices)s; ' +
                              'default: %(default)s)'))


def add_build_args(parser):
    backends = list_backends()
    install_dirs = platform_info().install_dirs
    path_help = 'installation path for {} (default: %(default)r)'

    parser.add_argument('--backend', metavar='BACKEND',
                        choices=list(backends.keys()),
                        default=list(backends.keys())[0],
                        help=('build backend (one of %(choices)s; default: ' +
                              '%(default)s)'))
    parser.add_argument('--prefix', type=abspath, metavar='PATH',
                        default=install_dirs[InstallRoot.prefix],
                        help='installation prefix (default: %(default)r)')
    parser.add_argument('--bindir', type=abspath, metavar='PATH',
                        default=install_dirs[InstallRoot.bindir],
                        help=path_help.format('executables'))
    parser.add_argument('--libdir', type=abspath, metavar='PATH',
                        default=install_dirs[InstallRoot.libdir],
                        help=path_help.format('libraries'))
    parser.add_argument('--includedir', type=abspath, metavar='PATH',
                        default=install_dirs[InstallRoot.includedir],
                        help=path_help.format('headers'))


def build(parser, args):
    srcstr = args.srcdir.string()
    buildstr = args.builddir.string()

    if samefile(srcstr, buildstr):
        parser.error('source and build directories must be different')
    if not is_srcdir(srcstr):
        parser.error('source directory must contain a {} file'
                     .format(bfgfile))
    if is_srcdir(buildstr):
        parser.error('build directory must not contain a {} file'
                     .format(bfgfile))

    if not os.path.exists(buildstr):
        os.mkdir(buildstr)

    backend = list_backends()[args.backend]

    # De-munge the entry point if we're on Windows.
    bfgpath = Path(os.path.realpath(
        re.sub('-script.py$', '.exe', sys.argv[0])
    ))

    env = Environment(
        bfgpath=bfgpath,
        backend=args.backend,
        backend_version=backend.version(),
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
    backend.write(env, build)


def regenerate(parser, args):
    if is_srcdir(args.builddir.string()):
        parser.error('build directory must not contain a {} file'
                     .format(bfgfile))

    try:
        env = Environment.load(args.builddir.string())

        backend = list_backends()[env.backend]
        build = execute_script(env)
        backend.write(env, build)
    except Exception as e:
        msg = 'Unable to reload environment'
        if str(e):
            msg += ': {}'.format(str(e))
        if isinstance(e, EnvVersionError):
            msg += '\n  Please re-run bfg9000 manually'
        logger.error(msg)
        return 1


def main():
    parser = argparse.ArgumentParser(prog='bfg9000', description=description)
    add_generic_args(parser)

    subparsers = parser.add_subparsers()

    buildp = subparsers.add_parser('build', description=build_desc,
                                   help='create build files')
    buildp.set_defaults(func=build)
    buildp.add_argument('directory', metavar='DIRECTORY', action=DirectoryPair,
                        help='source or build directory')
    add_build_args(buildp)

    buildexp = subparsers.add_parser('buildex', description=buildex_desc,
                                     help='create build files')
    buildexp.add_argument('srcdir', metavar='SRCDIR', action=ExistingDirectory,
                          help='source directory')
    buildexp.add_argument('builddir', metavar='BUILDDIR', action=Directory,
                          help='build directory')
    buildexp.set_defaults(func=build)
    add_build_args(buildexp)

    regenp = subparsers.add_parser('regenerate', description=regenerate_desc,
                                   help='regenerate build files')
    regenp.set_defaults(func=regenerate)
    regenp.add_argument('builddir', metavar='BUILDDIR', nargs='?', default='.',
                        action=ExistingDirectory, help='build directory')

    args = parser.parse_args()
    log.init(args.color, debug=args.debug)

    return args.func(parser, args)


def simple_main():
    parser = argparse.ArgumentParser(prog='9k', description=build_desc)
    parser.add_argument('directory', metavar='DIRECTORY', action=DirectoryPair,
                        help='source or build directory')
    add_generic_args(parser)
    add_build_args(parser)

    args = parser.parse_args()
    log.init(args.color, debug=args.debug)

    return build(parser, args)
