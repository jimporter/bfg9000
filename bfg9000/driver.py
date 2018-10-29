import os
import sys
from six import iteritems

from . import build
from . import log
from . import path
from .arguments import parser as argparse
from .backends import list_backends
from .environment import Environment, EnvVersionError
from .platforms.target import platform_info
from .app_version import version

logger = log.getLogger(__name__)

description = """
bfg9000 ("build file generator") is a cross-platform build configuration system
with an emphasis on making it easy to define how to build your software. It
converts a Python-based build script into the appropriate files for your
underlying build system of choice.
"""

configure_desc = """
Generate the necessary build files to perform actual builds. If DIRECTORY is a
source directory (i.e. it contains a build.bfg file), the build files will be
created in the current directory. Otherwise, DIRECTORY is treated as the build
directory, and bfg9000 will look for a build.bfg file in the current directory.
"""

configureinto_desc = """
Generate the necessary build files to perform actual builds from a build.bfg
file in SRCDIR, and place them in BUILDDIR.
"""

refresh_desc = """
Regenerate an existing set of build files needed to perform actual builds. This
is run automatically if bfg9000 determines that the build files are out of
date.
"""

env_desc = """
Print the environment variables stored by this build configuration.
"""


def handle_reload_exception(e, suggest_rerun=False):
    msg = 'Unable to reload environment'
    if str(e):
        msg += ': {}'.format(str(e))
    if suggest_rerun and isinstance(e, EnvVersionError):
        msg += '\n  Please re-run bfg9000 manually'
    logger.error(msg, exc_info=True)
    return 1


def environment_from_args(args, extra_args=None):
    # Get the bin directory holding bfg's executables.
    bfgdir = path.abspath(sys.argv[0]).parent()

    backend = list_backends()[args.backend]
    env = Environment(
        bfgdir=bfgdir,
        backend=args.backend,
        backend_version=backend.version(),
        srcdir=args.srcdir,
        builddir=args.builddir,
        install_dirs={i: getattr(args, i.name) for i in path.InstallRoot},
        library_mode=(args.shared, args.static),
        extra_args=extra_args,
    )

    return env, backend


def directory_pair(srcname, buildname):
    class DirectoryPair(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            cwd = path.abspath('.')

            if build.is_srcdir(values):
                srcdir, builddir = values, cwd
            else:
                srcdir, builddir = cwd, values

            setattr(namespace, srcname, srcdir)
            setattr(namespace, buildname, builddir)

    return DirectoryPair


class ConfigureHelp(argparse.Action):
    def __init__(self, option_strings, dest=argparse.SUPPRESS,
                 default=argparse.SUPPRESS, help=None):
        argparse.Action.__init__(
            self, option_strings=option_strings, dest=dest, default=default,
            nargs=0, help=help
        )

    def __call__(self, parser, namespace, values, option_string=None):
        cwd = path.abspath('.')
        if not hasattr(namespace, 'srcdir') and build.is_srcdir(cwd):
            namespace.srcdir = cwd
            namespace.builddir = None

        if getattr(namespace, 'srcdir', None):
            env, backend = environment_from_args(namespace)
            build.print_user_help(env, parser)
        else:
            parser.print_help()
        parser.exit()


def add_generic_args(parser):
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + version)
    parser.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--color', metavar='WHEN',
                        choices=['always', 'never', 'auto'], default='auto',
                        help=('show colored output (one of: %(choices)s; ' +
                              'default: %(default)s)'))
    parser.add_argument('-c', action='store_const', const='always',
                        dest='color',
                        help=('show colored output (equivalent to ' +
                              '`--color=always`)'))
    parser.add_argument('--warn-once', action='store_true',
                        help='only emit a given warning once')


def add_configure_args(parser):
    backends = list_backends()

    parser.add_argument('-h', '--help', action=ConfigureHelp,
                        help='show this help message and exit')

    build = parser.add_argument_group('build arguments')
    build.add_argument('--backend', metavar='BACKEND',
                       choices=list(backends.keys()),
                       default=list(backends.keys())[0],
                       help=('build backend (one of %(choices)s; default: ' +
                             '%(default)s)'))
    build.add_argument('--toolchain', metavar='FILE',
                       type=argparse.File(must_exist=True),
                       help=('a file defining the toolchain to use for this ' +
                             'build'))
    build.add_argument('--shared', action='enable', default=True,
                       help='build shared libraries (default: enabled)')
    build.add_argument('--static', action='enable', default=False,
                       help='build static libraries (default: disabled)')

    install_dirs = platform_info().install_dirs
    common_path_help = 'installation path for {} (default: %(default)r)'
    path_help = {
        'prefix': 'installation prefix (default: %(default)r)',
        'exec_prefix': ('installation prefix for architecture-dependent ' +
                        'files (default: %(default)r)'),
        'bindir': common_path_help.format('executables'),
        'libdir': common_path_help.format('libraries'),
        'includedir': common_path_help.format('headers'),
    }

    install = parser.add_argument_group('installation arguments')
    for root in path.InstallRoot:
        name = '--' + root.name.replace('_', '-')
        install.add_argument(name, type=argparse.Directory(), metavar='PATH',
                             default=install_dirs[root],
                             help=path_help[root.name])


def configure(parser, subparser, args, extra):
    if ( path.exists(args.builddir) and
         path.samefile(args.srcdir, args.builddir) ):
        subparser.error('source and build directories must be different')
    if not build.is_srcdir(args.srcdir):
        subparser.error('source directory must contain a {} file'
                        .format(build.bfgfile))
    if build.is_srcdir(args.builddir):
        subparser.error('build directory must not contain a {} file'
                        .format(build.bfgfile))

    if not path.exists(args.builddir):
        os.mkdir(args.builddir.string())

    try:
        env, backend = environment_from_args(args, extra)
        if args.toolchain:
            build.load_toolchain(env, args.toolchain)
        env.save(args.builddir.string())

        argv = build.parse_user_args(env)
        build_inputs = build.execute_script(env, argv)
        backend.write(env, build_inputs)
    except Exception as e:
        logger.exception(e)
        return 1


def refresh(parser, subparser, args, extra):
    if extra:
        subparser.error('unrecognized arguments: {}'.format(' '.join(extra)))

    if build.is_srcdir(args.builddir):
        subparser.error('build directory must not contain a {} file'
                        .format(build.bfgfile))

    try:
        env = Environment.load(args.builddir.string())
        if env.toolchain.path:
            build.load_toolchain(env, env.toolchain.path, reload=True)
        env.save(args.builddir.string())

        backend = list_backends()[env.backend]
        argv = build.parse_user_args(env)
        build_inputs = build.execute_script(env, argv)
        backend.write(env, build_inputs)
    except Exception as e:
        return handle_reload_exception(e, suggest_rerun=True)


def env(parser, subparser, args, extra):
    if extra:
        subparser.error('unrecognized arguments: {}'.format(' '.join(extra)))

    if build.is_srcdir(args.builddir):
        subparser.error('build directory must not contain a {} file'
                        .format(build.bfgfile))

    try:
        env = Environment.load(args.builddir.string())

        for k, v in sorted(iteritems(env.variables)):
            if not args.unique or os.getenv(k) != v:
                print('{}={}'.format(k, v))
    except Exception as e:
        return handle_reload_exception(e)


def help(parser, subparser, args, extra):
    parser.parse_args(extra + ['--help'])


def main():
    parser = argparse.ArgumentParser(prog='bfg9000', description=description)
    subparsers = parser.add_subparsers(metavar='COMMAND')
    subparsers.required = True

    add_generic_args(parser)

    conf_p = subparsers.add_parser(
        'configure', description=configure_desc, add_help=False,
        help='create build files'
    )
    conf_p.set_defaults(func=configure, parser=conf_p)
    conf_p.add_argument(argparse.SUPPRESS,
                        action=directory_pair('srcdir', 'builddir'),
                        type=argparse.Directory(), metavar='DIRECTORY',
                        help='source or build directory')
    add_configure_args(conf_p)

    confinto_p = subparsers.add_parser(
        'configure-into', description=configureinto_desc, add_help=False,
        help='create build files in a chosen directory'
    )
    confinto_p.add_argument('srcdir', type=argparse.Directory(must_exist=True),
                            metavar='SRCDIR', help='source directory')
    confinto_p.add_argument('builddir', type=argparse.Directory(),
                            metavar='BUILDDIR', help='build directory')
    confinto_p.set_defaults(func=configure, parser=confinto_p)
    add_configure_args(confinto_p)

    refresh_p = subparsers.add_parser(
        'refresh', description=refresh_desc, help='regenerate build files'
    )
    refresh_p.set_defaults(func=refresh, parser=refresh_p)
    refresh_p.add_argument('builddir',
                           type=argparse.Directory(must_exist=True),
                           metavar='BUILDDIR', nargs='?', default='.',
                           help='build directory')

    env_p = subparsers.add_parser(
        'env', description=env_desc, help='print environment'
    )
    env_p.set_defaults(func=env, parser=env_p)
    env_p.add_argument('-u', '--unique', action='store_true',
                       help='only show variables that differ from the ' +
                       'current environment')
    env_p.add_argument('builddir', type=argparse.Directory(must_exist=True),
                       metavar='BUILDDIR', nargs='?', default='.',
                       help='build directory')

    help_p = subparsers.add_parser(
        'help', help='show this help message and exit', add_help=False
    )
    help_p.set_defaults(func=help, parser=help_p)

    args, extra = parser.parse_known_args()
    log.init(args.color, debug=args.debug, warn_once=args.warn_once)

    return args.func(parser, args.parser, args, extra)


def simple_main():
    parser = argparse.ArgumentParser(prog='9k', description=configure_desc,
                                     add_help=False)
    parser.add_argument(argparse.SUPPRESS,
                        action=directory_pair('srcdir', 'builddir'),
                        type=argparse.Directory(), metavar='DIRECTORY',
                        help='source or build directory')
    add_generic_args(parser)
    add_configure_args(parser)

    args, extra = parser.parse_known_args()
    log.init(args.color, debug=args.debug, warn_once=args.warn_once)

    return configure(parser, parser, args, extra)
