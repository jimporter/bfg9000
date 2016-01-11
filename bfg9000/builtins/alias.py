from . import builtin
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import Edge
from ..file_types import Phony


class Alias(Edge):
    def __init__(self, build, name, deps=None):
        Edge.__init__(self, build, Phony(name), deps)


@builtin.globals('build_inputs')
def alias(build, *args, **kwargs):
    return Alias(build, *args, **kwargs).target


@make.rule_handler(Alias)
def make_alias(rule, build_inputs, buildfile, env):
    buildfile.rule(
        target=rule.target,
        deps=rule.extra_deps,
        phony=True
    )


@ninja.rule_handler(Alias)
def ninja_alias(rule, build_inputs, buildfile, env):
    buildfile.build(
        output=rule.target,
        rule='phony',
        inputs=rule.extra_deps
    )
