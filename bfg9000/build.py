import errno

from .arguments.parser import ArgumentParser
from .builtins import builtin, init as builtin_init
from .build_inputs import BuildInputs
from .path import exists, Path, pushd, Root
from .iterutils import listify
from .tools import init as tools_init

bfgfile = 'build.bfg'
optsfile = 'options.bfg'

user_description = """
These arguments are defined by the options.bfg file in the project's source
directory. To disambiguate them from built-in arguments, you may prefix the
argument name with `-x`. For example, `--foo` may also be written as `--x-foo`.
"""


def is_srcdir(path):
    return exists(path.append(bfgfile))


def _execute_file(f, filename, builtin_dict):
    code = compile(f.read(), filename, 'exec')
    try:
        exec(code, builtin_dict)
    except SystemExit:
        pass


def load_toolchain(env, filename, reload=False):
    builtin_init()
    tools_init()

    if reload:
        env.init_variables()

    builtin_dict = builtin.toolchain.bind(env=env)
    with open(filename.string(), 'r') as f:
        _execute_file(f, f.name, builtin_dict)

    if not reload:
        env.toolchain.path = filename


def _fill_parser(env, parent=None, filename=optsfile, usage='parse'):
    builtin_init()

    optspath = Path(filename, Root.srcdir)
    prog = parent.prog if parent else filename

    parser = ArgumentParser(prog=prog, parents=listify(parent),
                            add_help=False)
    try:
        with open(optspath.string(env.base_dirs), 'r') as f, \
             pushd(env.srcdir.string()):  # noqa
            group = parser.add_argument_group('project-defined arguments',
                                              description=user_description)
            group.usage = usage

            builtin_dict = builtin.options.bind(env=env, parser=group)
            _execute_file(f, filename, builtin_dict)
            builtin.options.run_post(builtin_dict, env=env, parser=group)
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
    builtin_init()

    bfgpath = Path(filename, Root.srcdir)
    build = BuildInputs(env, bfgpath)
    builtin_dict = builtin.build.bind(build_inputs=build, argv=argv, env=env)

    with open(bfgpath.string(env.base_dirs), 'r') as f, \
         pushd(env.srcdir.string()):  # noqa
        _execute_file(f, filename, builtin_dict)
        builtin.build.run_post(builtin_dict, build_inputs=build, argv=argv,
                               env=env)
    return build
