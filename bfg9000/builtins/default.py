from . import builtin
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import build_input


@build_input('defaults')
class DefaultOutputs(object):
    def __init__(self, build_inputs, env):
        self.default_outputs = []
        self.fallback_defaults = []

    def add(self, output, explicit=False):
        outputs = self.default_outputs if explicit else self.fallback_defaults
        for i in output.all:
            if i.creator:
                outputs.append(i)

    def remove(self, output, explicit=False):
        outputs = self.default_outputs if explicit else self.fallback_defaults
        for i, fallback in enumerate(outputs):
            if output is fallback:
                self.fallback_defaults.pop(i)

    @property
    def outputs(self):
        return self.default_outputs or self.fallback_defaults


@builtin.function('build_inputs')
def default(build, *args):
    for i in args:
        build['defaults'].add(i, explicit=True)


@make.pre_rule
def make_all_rule(build_inputs, buildfile, env):
    buildfile.rule(
        target='all',
        deps=build_inputs['defaults'].outputs,
        phony=True
    )


@ninja.pre_rule
def ninja_all_rule(build_inputs, buildfile, env):
    buildfile.default(['all'])
    buildfile.build(
        output='all',
        rule='phony',
        inputs=build_inputs['defaults'].outputs,
    )
