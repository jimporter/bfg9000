from collections import namedtuple

from . import builtin
from .. import log
from ..backends import list_backends
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import build_input
from ..iterutils import listify
from ..path import Path


def _inputs(build_inputs, env):
    extra = []
    if env.mopack:
        extra = [env.tool('mopack').metadata_file]
    return build_inputs.bootstrap_paths + listify(env.toolchain.path) + extra


def _outputs(build_inputs, env):
    return ([list_backends()[env.backend].filepath] +
            [i.path for i in build_inputs['regenerate'].outputs])


@build_input('regenerate')
class Regenerate:
    def __init__(self):
        self.outputs = []
        self.depfile = None


# This class is used to help serialize the direct inputs/outputs for the
# `regenerate` build step so that we can consult it when determining whether to
# abort regeneration in `find_check_cache`.
class RegenerateFiles(namedtuple('RegenerateFiles', ['inputs', 'outputs'])):
    @classmethod
    def make(cls, build_inputs, env):
        return RegenerateFiles(_inputs(build_inputs, env),
                               _outputs(build_inputs, env))

    def to_json(self):
        return {
            'inputs': [i.to_json() for i in self.inputs],
            'outputs': [i.to_json() for i in self.outputs],
        }

    @classmethod
    def from_json(cls, data):
        return cls(
            [Path.from_json(i) for i in data['inputs']],
            [Path.from_json(i) for i in data['outputs']],
        )


@builtin.execute_hook()
def log_regenerating(context):
    if context.regenerating:
        log.info('regenerating build files')


@make.post_rules_hook
def make_regenerate_rule(build_inputs, buildfile, env):
    bfg9000 = env.tool('bfg9000')

    if env.mopack:
        mopack = env.tool('mopack')
        buildfile.rule(
            target=mopack.metadata_file,
            deps=env.mopack + listify(env.toolchain.path),
            recipe=[bfg9000('run', initial=True, args=mopack(
                'resolve', env.mopack, directory=Path('.')
            ))]
        )

    make.multitarget_rule(
        build_inputs, buildfile,
        targets=_outputs(build_inputs, env),
        deps=_inputs(build_inputs, env),
        recipe=[bfg9000('regenerate', lazy=True)],
        clean_stamp=False
    )


@ninja.post_rules_hook
def ninja_regenerate_rule(build_inputs, buildfile, env):
    bfg9000 = env.tool('bfg9000')
    rule_kwargs = {}
    if ninja.features.supported('console', env.backend_version):
        rule_kwargs['pool'] = 'console'

    if env.mopack:
        mopack = env.tool('mopack')
        buildfile.rule(
            name='regenerate_deps',
            command=bfg9000('run', initial=True, args=mopack(
                'resolve', ninja.var('in'), directory=Path('.')
            )),
            generator=True,
            description='regenerate dependencies',
            **rule_kwargs
        )
        buildfile.build(
            output=mopack.metadata_file,
            rule='regenerate_deps',
            inputs=env.mopack,
            implicit=listify(env.toolchain.path)
        )

    buildfile.rule(
        name='regenerate',
        command=bfg9000('regenerate', lazy=True),
        generator=True,
        depfile=build_inputs['regenerate'].depfile,
        description='regenerate',
        **rule_kwargs
    )
    buildfile.build(
        output=_outputs(build_inputs, env),
        rule='regenerate',
        implicit=_inputs(build_inputs, env)
    )
