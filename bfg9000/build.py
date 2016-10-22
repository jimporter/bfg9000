import os

from . import builtins
from .build_inputs import BuildInputs
from .path import Path, pushd, Root

bfgfile = 'build.bfg'


def is_srcdir(path):
    return os.path.exists(os.path.join(path, bfgfile))


def execute_script(env, filename=bfgfile):
    bfgpath = Path(filename, Root.srcdir)
    build = BuildInputs(env, bfgpath)
    builtin_dict = builtins.bind(build_inputs=build, env=env)

    with open(bfgpath.string(env.path_roots), 'r') as f, \
         pushd(env.srcdir.string()):  # noqa
        code = compile(f.read(), filename, 'exec')
        try:
            exec(code, builtin_dict)
        except SystemExit:
            pass

    return build


