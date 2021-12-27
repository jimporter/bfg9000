import errno
from itertools import chain

from . import log
from .arguments.parser import ArgumentParser
from .builtins import builtin, init as builtin_init
from .build_inputs import BuildInputs
from .iterutils import listify
from .path import exists, Path, pushd, Root
from .shell import Mode
from .tools import init as tools_init, mopack

bfgfile = 'build.bfg'
optsfile = 'options.bfg'

user_description = """
These arguments are defined by the options.bfg file in the project's source
directory. To disambiguate them from built-in arguments, you may prefix the
argument name with `-x`. For example, `--foo` may also be written as `--x-foo`.
"""


class ScriptExitError(RuntimeError):
    def __init__(self, path, code):
        super().__init__('{} failed with exit status {}'.format(path, code))
        self.code = code


def is_srcdir(path):
    return exists(path.append(bfgfile))


def _execute_script(f, context, path, run_post=False):
    filename = path.string(context.env.base_dirs)

    with pushd(path.parent().string(context.env.base_dirs)), \
         context.push_path(path) as p:
        code = compile(f.read(), filename, 'exec')
        try:
            exec(code, context.builtins)
        except SystemExit as e:
            if e.code:
                raise ScriptExitError(filename, e.code)

        if run_post:
            context.run_post()
        return p


def execute_file(context, path, run_post=False):
    with open(path.string(context.env.base_dirs), 'r') as f:
        return _execute_script(f, context, path, run_post)


def load_toolchain(env, path, reload=False):
    builtin_init()
    tools_init()
    if reload:
        env.reload()
    else:
        env.toolchain.path = path

    context = builtin.ToolchainContext(env, reload)
    execute_file(context, path, run_post=True)


def _execute_options(env, parent=None, usage='parse'):
    optspath = Path(builtin.OptionsContext.filename, Root.srcdir)
    prog = parent.prog if parent else optspath.basename()
    parser = ArgumentParser(prog=prog, parents=listify(parent), add_help=False)

    try:
        with open(optspath.string(env.base_dirs), 'r') as f:
            group = parser.add_argument_group('project-defined arguments',
                                              description=user_description)
            group.usage = usage

            context = builtin.OptionsContext(env, group)
            _execute_script(f, context, optspath, run_post=True)
            return parser, context.seen_paths
    except IOError as e:
        if e.errno != errno.ENOENT:
            raise
        return parser, []


def resolve_packages(env, files, flags):
    if env.variables.initial.get('MOPACK_NESTED_INVOCATION'):
        return []

    log.info('resolving package dependencies...')
    mopack_files = ( [Path('.', Root.srcdir)] +
                     listify(mopack.make_options_yml(env)) +
                     (files or []) )
    env.tool('mopack').run(
        'resolve', mopack_files, directory=env.builddir, flags=flags,
        env=env.variables.initial, stdout=Mode.normal
    )
    # TODO: Would it make sense to convert these paths into ones relative to
    # the source/build directories if possible?
    return [Path(i, Root.absolute) for i in
            env.tool('mopack').run('list_files', directory=env.builddir)]


def fill_user_help(env, parent):
    builtin_init()
    return _execute_options(env, parent, usage='help')[0]


def configure_build(env):
    builtin_init()
    parser, opts_paths = _execute_options(env)
    argv = parser.parse_args(env.extra_args)

    bfgpath = Path(builtin.BuildContext.filename, Root.srcdir)
    build = BuildInputs(env, bfgpath)
    context = builtin.BuildContext(env, build, argv)
    execute_file(context, bfgpath, run_post=True)

    # Add all the bfg files as bootstrap entries (except for the main
    # build.bfg, which is already included).
    for i in chain(context.seen_paths[1:], opts_paths):
        build.add_bootstrap(i)

    return build
