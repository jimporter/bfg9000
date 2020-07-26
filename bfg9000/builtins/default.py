from . import builtin
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import build_input
from ..iterutils import iterate_each, unlistify


@build_input('defaults')
class DefaultOutputs:
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
        for i, v in enumerate(outputs):
            if output is v:
                outputs.pop(i)

    @property
    def outputs(self):
        return self.default_outputs or self.fallback_defaults


@builtin.function()
def default(context, *args):
    for i in iterate_each(args):
        context.build['defaults'].add(i, explicit=True)
    return unlistify(args)


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


try:
    from ..backends.msbuild import writer as msbuild

    @msbuild.post_rule
    def msbuild_default(build_inputs, solution, env):
        # Default builds go first in the solution. As a partial implementation,
        # we treat the first explicit default or the last implicit default as
        # the "default project". XXX: For full support, we'd need to support
        # aliases so that we can have multiple builds be the default.
        defaults = build_inputs['defaults']
        if defaults.default_outputs:
            solution.set_default(defaults.default_outputs[0])
        elif defaults.fallback_defaults:
            solution.set_default(defaults.fallback_defaults[-1])
except ImportError:  # pragma: no cover
    pass
