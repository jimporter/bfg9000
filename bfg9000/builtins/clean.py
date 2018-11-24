from ..backends.make import writer as make


@make.post_rule
def make_clean_rule(build_inputs, buildfile, env):
    rm = env.tool('rm')
    buildfile.rule(target='clean', recipe=[
        rm(i.path for i in build_inputs.targets())
    ], phony=True)
