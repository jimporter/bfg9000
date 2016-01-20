from .hooks import builtin
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import build_input


@build_input('defaults')
class DefaultTargets(object):
    def __init__(self):
        self.default_targets = []
        self.fallback_defaults = []

    def add(self, target, explicit=False):
        targets = self.default_targets if explicit else self.fallback_defaults
        targets.append(target)

    def remove(self, target):
        for i, fallback in enumerate(self.fallback_defaults):
            if target is fallback:
                self.fallback_defaults.pop(i)

    @property
    def targets(self):
        return self.default_targets or self.fallback_defaults


@builtin.globals('build_inputs')
def default(build, *args):
    for i in args:
        if i.creator:
            build['defaults'].add(i, explicit=True)


@make.pre_rule
def make_all_rule(build_inputs, buildfile, env):
    buildfile.rule(
        target='all',
        deps=build_inputs['defaults'].targets,
        phony=True
    )


@ninja.pre_rule
def ninja_all_rule(build_inputs, buildfile, env):
    buildfile.default(['all'])
    buildfile.build(
        output='all',
        rule='phony',
        inputs=build_inputs['defaults'].targets,
    )
