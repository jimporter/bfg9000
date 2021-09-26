import os
import subprocess
import sys

from . import build, log, path
from .app_version import version
from .arguments import parser as argparse
from .backends import list_backends
from .backends.compdb import writer as compdb
from .environment import Environment, EnvVersionError
from .platforms.target import platform_info

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

run_desc = """
Run an arbitrary COMMAND with the environment variables set for the current
build.
"""

e1m1_desc = """
You find yourself standing at Doom's gate.
"""

generate_completion_desc = """
Generate shell-completion functions for bfg9000 and write them to standard
output. This requires the Python package `shtab`.
"""


def handle_reload_exception(e, suggest_rerun=False):
    msg = 'unable to reload environment'
    if str(e):
        msg += ': {}'.format(str(e))
    if suggest_rerun and isinstance(e, EnvVersionError):
        msg += '\n  please re-run bfg9000 manually'
    logger.error(msg, exc_info=True)
    return e.code if isinstance(e, build.ScriptExitError) else 1


def environment_from_args(args):
    # Get the bin directory holding bfg's executables.
    bfgdir = path.abspath(sys.argv[0]).parent()

    backend = list_backends()[args.backend]
    env = Environment(
        bfgdir=bfgdir,
        backend=args.backend,
        backend_version=backend.version(),
        srcdir=args.srcdir,
        builddir=args.builddir,
    )

    return env, backend


def finalize_environment(env, args, extra_args=None):
    env.finalize(
        install_dirs={i: getattr(args, i.name) for i in path.InstallRoot},
        library_mode=(args.shared, args.static),
        compdb=args.compdb,
        extra_args=extra_args,
    )


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
        super().__init__(option_strings=option_strings, dest=dest,
                         default=default, nargs=0, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        cwd = path.abspath('.')
        if not hasattr(namespace, 'srcdir') and build.is_srcdir(cwd):
            namespace.srcdir = cwd
            namespace.builddir = None

        if getattr(namespace, 'srcdir', None):
            env, backend = environment_from_args(namespace)
            parser = build.fill_user_help(env, parser)

        parser.print_help()
        parser.exit()


def add_generic_args(parser):
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + version)
    parser.add_argument('--debug', action='store_true',
                        help='report extra information for debugging bfg9000')
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
    build.add_argument('-B', '--backend', metavar='BACKEND',
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
    build.add_argument('--compdb', action='enable', default=True,
                       help=('generate compile_commands.json ' +
                             '(default: enabled)'))

    pkg = parser.add_argument_group('packaging arguments')
    pkg.add_argument('-p', '--package-file', action='append', metavar='FILE',
                     dest='package_files',
                     help='additional package files to resolve')
    pkg.add_argument('-P', '--package-flag', action='append',
                     metavar='FLAG', dest='package_flags',
                     help='additional package flags')
    pkg.add_argument('--no-resolve-packages', action='store_true',
                     help='skip resolution of packages')

    common_path_help = 'installation path for {} (default: {{}})'
    path_help = {
        'prefix': 'installation prefix (default: {})',
        'exec_prefix': ('installation prefix for architecture-dependent ' +
                        'files (default: {})'),
        'bindir'    : common_path_help.format('executables'),
        'libdir'    : common_path_help.format('libraries'),
        'includedir': common_path_help.format('headers'),
        'datadir'   : common_path_help.format('data files'),
        'mandir'    : common_path_help.format('man pages'),
    }

    install_dirs = platform_info().install_dirs
    install = parser.add_argument_group('installation arguments')
    for root in path.InstallRoot:
        name = '--' + root.name.replace('_', '-')
        help = path_help[root.name].format(repr(install_dirs[root]))
        install.add_argument(name, type=argparse.Directory(), metavar='PATH',
                             help=help)


def simple_parser():
    parser = argparse.ArgumentParser(prog='9k', description=configure_desc,
                                     add_help=False)
    parser.add_argument(argparse.SUPPRESS,
                        action=directory_pair('srcdir', 'builddir'),
                        type=argparse.Directory(), metavar='DIRECTORY',
                        help='source or build directory')
    add_generic_args(parser)
    add_configure_args(parser)

    return parser


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

    os.makedirs(args.builddir.string(), exist_ok=True)

    try:
        env, backend = environment_from_args(args)
        if args.toolchain:
            build.load_toolchain(env, args.toolchain)
        finalize_environment(env, args, extra)

        if not args.no_resolve_packages:
            env.mopack = build.resolve_packages(env, args.package_files,
                                                args.package_flags)

        env.save(args.builddir.string())

        build_inputs = build.configure_build(env)
        backend.write(env, build_inputs)
        if env.compdb:
            compdb.write(env, build_inputs)
    except Exception as e:
        logger.exception(e)
        return e.code if isinstance(e, build.ScriptExitError) else 1


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
        build_inputs = build.configure_build(env)
        backend.write(env, build_inputs)
        if env.compdb:
            compdb.write(env, build_inputs)
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

        for k, v in sorted(env.variables.items()):
            if not args.unique or os.getenv(k) != v:
                print('{}={}'.format(k, v))
    except Exception as e:
        return handle_reload_exception(e)


def run(parser, subparser, args, extra):
    if extra:
        subparser.error('unrecognized arguments: {}'.format(' '.join(extra)))

    if build.is_srcdir(args.builddir):
        subparser.error('build directory must not contain a {} file'
                        .format(build.bfgfile))

    try:
        env = Environment.load(args.builddir.string())
        cmd = args.command
        if cmd and cmd[0] == '--':
            cmd = cmd[1:]
        if len(cmd) == 0:
            parser.error('command required')

        variables = env.variables.initial if args.initial else env.variables
        return subprocess.run(cmd, env=variables).returncode
    except Exception as e:
        return handle_reload_exception(e)


def e1m1(parser, subparser, args, extra):  # pragma: no cover
    import e1m1
    try:
        e1m1.play(args.tempo, args.long)
    except Exception as e:
        logger.exception(e)
        return 1


def help(parser, subparser, args, extra):
    parser.parse_args(extra + ['--help'])


def generate_completion(parser, subparser, args, extra):
    if extra:
        subparser.error('unrecognized arguments: {}'.format(' '.join(extra)))

    try:
        import shtab
        p = parser if args.program == 'bfg9000' else simple_parser()
        print(shtab.complete(p, shell=args.shell))
    except ImportError:  # pragma: no cover
        print('shtab not found; install via `pip install shtab`')
        return 1


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
                       help=('only show variables that differ from the ' +
                             'current environment'))
    env_p.add_argument('builddir', type=argparse.Directory(must_exist=True),
                       metavar='BUILDDIR', nargs='?', default='.',
                       help='build directory')

    run_p = subparsers.add_parser(
        'run', description=run_desc, help='run a shell command'
    )
    run_p.set_defaults(func=run, parser=run_p)
    run_p.add_argument('-I', '--initial', action='store_true',
                       help='use initial environment variable state')
    run_p.add_argument('-B', '--builddir',
                       type=argparse.Directory(must_exist=True),
                       metavar='BUILDDIR', default='.', help='build directory')
    run_p.add_argument('command', metavar='COMMAND', nargs=argparse.REMAINDER,
                       help='command argument')

    e1m1_p = subparsers.add_parser('e1m1', description=e1m1_desc)
    e1m1_p.set_defaults(func=e1m1, parser=e1m1_p)
    # Windows gets glitchy if we play back too fast...
    tempo = 100 if platform_info().family == 'windows' else 120
    e1m1_p.add_argument('-t', '--tempo', metavar='BPM', type=int,
                        default=tempo,
                        help='playback speed (default: %(default)s)')
    e1m1_p.add_argument('-L', '--long', action='store_true',
                        help='play for longer')

    help_p = subparsers.add_parser(
        'help', help='show this help message and exit', add_help=False
    )
    help_p.set_defaults(func=help, parser=help_p)

    completion_p = subparsers.add_parser(
        'generate-completion', description=generate_completion_desc,
        help='print shell completion script'
    )
    completion_p.set_defaults(func=generate_completion, parser=completion_p)
    shell = (os.path.basename(os.environ['SHELL'])
             if 'SHELL' in os.environ else None)
    completion_p.add_argument('-p', '--program', metavar='PROG',
                              default='bfg9000', choices=['bfg9000', '9k'],
                              help=('program to emit completion for (one of ' +
                                    '%(choices)s; default: %(default)s)'))
    completion_p.add_argument('-s', '--shell', metavar='SHELL', default=shell,
                              help='shell type (default: %(default)s)')

    args, extra = parser.parse_known_args()
    log.init(args.color, debug=args.debug, warn_once=args.warn_once)

    return args.func(parser, args.parser, args, extra)


def simple_main():
    parser = simple_parser()

    args, extra = parser.parse_known_args()
    log.init(args.color, debug=args.debug, warn_once=args.warn_once)

    return configure(parser, parser, args, extra)
