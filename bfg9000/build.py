import errno
import os

from .builtins import builtin, optbuiltin, user_arguments
from .build_inputs import BuildInputs
from .path import Path, pushd, Root
from .iterutils import listify

bfgfile = 'build.bfg'
optsfile = 'build.opts'


def is_srcdir(path):
    return os.path.exists(os.path.join(path, bfgfile))


def _fill_parser(env, parent=None, filename=optsfile, usage='parse'):
    optspath = Path(filename, Root.srcdir)
    prog = parent.prog if parent else filename
    parser, group = user_arguments.make_parser(prog, listify(parent),
                                               usage=usage)
    builtin_dict = optbuiltin.bind(env=env, parser=group)

    try:
        with open(optspath.string(env.path_roots), 'r') as f, \
             pushd(env.srcdir.string()):  # noqa:
            code = compile(f.read(), filename, 'exec')
            exec(code, builtin_dict)
    except SystemExit:
        pass
    except IOError as e:
        if e.errno != errno.ENOENT:
            raise

    return parser


def print_help(env, parent, filename=optsfile, out=None):
    parser = _fill_parser(env, parent, filename, usage='help')
    parser.print_help(out)


def parse_extra_args(env, filename=optsfile):
    parser = _fill_parser(env, None, filename)
    return parser.parse_args(env.extra_args)


def execute_script(env, argv, filename=bfgfile):
    bfgpath = Path(filename, Root.srcdir)
    build = BuildInputs(env, bfgpath)
    builtin_dict = builtin.bind(build_inputs=build, argv=argv, env=env)

    with open(bfgpath.string(env.path_roots), 'r') as f, \
         pushd(env.srcdir.string()):  # noqa
        code = compile(f.read(), filename, 'exec')
        try:
            exec(code, builtin_dict)
        except SystemExit:
            pass

    return build
