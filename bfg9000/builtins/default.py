from . import builtin
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja


@builtin.globals('build_inputs')
def default(build, *args):
    if len(args) == 0:
        raise ValueError('expected at least one argument')
    build.default_targets.extend(i for i in args if i.creator)


@make.pre_rule
def make_all_rule(build_inputs, buildfile, env):
    buildfile.rule(
        target='all',
        deps=build_inputs.get_default_targets(),
        phony=True
    )


@ninja.pre_rule
def ninja_all_rule(build_inputs, buildfile, env):
    buildfile.default(['all'])
    buildfile.build(
        output='all',
        rule='phony',
        inputs=build_inputs.get_default_targets()
    )
