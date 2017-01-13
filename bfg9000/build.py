import errno
import os

from .arguments.parser import ArgumentParser
from .builtins import builtin, optbuiltin, user_arguments
from .build_inputs import BuildInputs
from .path import exists, Path, pushd, Root
from .iterutils import listify

bfgfile = 'build.bfg'
optsfile = 'build.opts'

user_description = """
These arguments are defined by the build.opts file in the project's source
directory. To disambiguate them from built-in arguments, you may prefix the
argument name with `-x`. For example, `--foo` may also be written as `--x-foo`.
"""


def is_srcdir(path):
    return exists(path.append(bfgfile))


def _fill_parser(env, parent=None, filename=optsfile, usage='parse'):
    optspath = Path(filename, Root.srcdir)
    prog = parent.prog if parent else filename

    parser = ArgumentParser(prog=prog, parents=listify(parent),
                            add_help=False)
    group = parser.add_argument_group('project-defined arguments',
                                      description=user_description)
    group.usage = usage

    builtin_dict = optbuiltin.bind(env=env, parser=group)
    try:
        with open(optspath.string(env.base_dirs), 'r') as f, \
             pushd(env.srcdir.string()):  # noqa
            code = compile(f.read(), filename, 'exec')
            exec(code, builtin_dict)
    except SystemExit:
        pass
    except IOError as e:
        if e.errno != errno.ENOENT:
            raise

    return parser


def print_user_help(env, parent, filename=optsfile, out=None):
    parser = _fill_parser(env, parent, filename, usage='help')
    parser.print_help(out)


def parse_user_args(env, filename=optsfile):
    parser = _fill_parser(env, None, filename)
    return parser.parse_args(env.extra_args)


def execute_script(env, argv, filename=bfgfile):
    bfgpath = Path(filename, Root.srcdir)
    build = BuildInputs(env, bfgpath)
    builtin_dict = builtin.bind(build_inputs=build, argv=argv, env=env)

    with open(bfgpath.string(env.base_dirs), 'r') as f, \
         pushd(env.srcdir.string()):  # noqa
        code = compile(f.read(), filename, 'exec')
        try:
            exec(code, builtin_dict)
        except SystemExit:
            pass

    return build
