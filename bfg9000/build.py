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

    builtin_dict = builtin.toolchain.bind(env=env, reload=reload)
    with open(filename.string(), 'r') as f:
        _execute_file(f, f.name, builtin_dict)

    if not reload:
        env.toolchain.path = filename


def _execute_options(env, optspath, parent=None, usage='parse'):
    prog = parent.prog if parent else optspath.basename()
    parser = ArgumentParser(prog=prog, parents=listify(parent),
                            add_help=False)
    executed = False

    try:
        with open(optspath.string(env.base_dirs), 'r') as f, \
             pushd(env.srcdir.string()):  # noqa
            group = parser.add_argument_group('project-defined arguments',
                                              description=user_description)
            group.usage = usage

            builtin_dict = builtin.options.bind(env=env, parser=group)
            _execute_file(f, optspath.basename(), builtin_dict)
            builtin.options.run_post(builtin_dict, env=env, parser=group)
        executed = True
    except IOError as e:
        if e.errno != errno.ENOENT:
            raise

    return parser, executed


def _execute_configure(env, argv, bfgpath, extra_bootstrap=[]):
    build = BuildInputs(env, bfgpath, extra_bootstrap)
    builtin_dict = builtin.build.bind(build_inputs=build, argv=argv, env=env)

    with open(bfgpath.string(env.base_dirs), 'r') as f, \
         pushd(env.srcdir.string()):  # noqa
        _execute_file(f, bfgpath.basename(), builtin_dict)
        builtin.build.run_post(builtin_dict, build_inputs=build, argv=argv,
                               env=env)
    return build


def fill_user_help(env, parent, filename=optsfile):
    builtin_init()
    optspath = Path(filename, Root.srcdir)
    return _execute_options(env, optspath, parent, usage='help')[0]


def configure_build(env, bfgfile=bfgfile, optsfile=optsfile):
    builtin_init()
    bfgpath = Path(bfgfile, Root.srcdir)
    optspath = Path(optsfile, Root.srcdir)

    parser, executed = _execute_options(env, optspath)
    argv = parser.parse_args(env.extra_args)

    extra_bootstrap = [optspath] if executed else []
    return _execute_configure(env, argv, bfgpath, extra_bootstrap)
