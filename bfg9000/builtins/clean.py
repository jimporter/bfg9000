from .. import shell
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..path import Path


def _clean_mopack(env):
    if env.mopack:
        return [env.tool('mopack')('clean', directory=Path('.'))]
    return []


@make.post_rule
def make_clean_rule(build_inputs, buildfile, env):
    rm = env.tool('rm')
    buildfile.rule(target='clean', recipe=(
        [rm(i.path for i in build_inputs.targets())] +
        _clean_mopack(env)
    ), phony=True)


@ninja.post_rule
def ninja_clean_rule(build_inputs, buildfile, env):
    ninja_cmd = buildfile.variable('ninja', ninja.executable(env.variables),
                                   buildfile.Section.command, True)
    ninja.command_build(
        buildfile, env,
        output='clean',
        command=shell.join_lines(
            [[ninja_cmd, '-t', 'clean']] +
            _clean_mopack(env)
        ),
        phony=True
    )
