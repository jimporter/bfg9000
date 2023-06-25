from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import build_input
from ..iterutils import listify
from ..path import Path


@build_input('regenerate')
class Regenerate:
    def __init__(self):
        self.outputs = []
        self.depfile = None


@make.post_rules_hook
def make_regenerate_rule(build_inputs, buildfile, env):
    bfg9000 = env.tool('bfg9000')

    extra_deps = []
    if env.mopack:
        mopack = env.tool('mopack')
        extra_deps = [mopack.metadata_file]
        buildfile.rule(
            target=mopack.metadata_file,
            deps=env.mopack + listify(env.toolchain.path),
            recipe=[bfg9000('run', initial=True, args=mopack(
                'resolve', env.mopack, directory=Path('.')
            ))]
        )

    make.multitarget_rule(
        build_inputs, buildfile,
        targets=[Path('Makefile')] + build_inputs['regenerate'].outputs,
        deps=(build_inputs.bootstrap_paths + listify(env.toolchain.path) +
              extra_deps),
        recipe=[bfg9000('regenerate', Path('.'))],
        clean_stamp=False
    )


@ninja.post_rules_hook
def ninja_regenerate_rule(build_inputs, buildfile, env):
    bfg9000 = env.tool('bfg9000')
    rule_kwargs = {}
    if ninja.features.supported('console', env.backend_version):
        rule_kwargs['pool'] = 'console'

    extra_deps = []
    if env.mopack:
        mopack = env.tool('mopack')
        extra_deps = [mopack.metadata_file]
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
        command=bfg9000('regenerate', Path('.')),
        generator=True,
        depfile=build_inputs['regenerate'].depfile,
        description='regenerate',
        **rule_kwargs
    )
    buildfile.build(
        output=[Path('build.ninja')] + build_inputs['regenerate'].outputs,
        rule='regenerate',
        implicit=(build_inputs.bootstrap_paths + listify(env.toolchain.path) +
                  extra_deps)
    )
