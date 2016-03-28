from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import Edge


class Symlink(Edge):
    def __init__(self, build, output, real):
        self.real = real
        self.link = real.path.relpath(output.path.parent())
        Edge.__init__(self, build, output)


@make.rule_handler(Symlink)
def make_symlink(rule, build_inputs, buildfile, env):
    recipename = make.var('SYMLINK')
    if not buildfile.has_variable(recipename):
        buildfile.define(recipename, [
            ['ln', '-sf', make.var('1'), make.qvar('@')],
        ])

    buildfile.rule(
        target=rule.output,
        deps=rule.real,
        recipe=make.Call(recipename, rule.link)
    )


@ninja.rule_handler(Symlink)
def ninja_symlink(rule, build_inputs, buildfile, env):
    if not buildfile.has_rule('symlink'):
        buildfile.rule(
            name='symlink',
            command=['ln', '-sf', ninja.var('input'), ninja.var('out')]
        )

    buildfile.build(
        output=rule.output,
        rule='symlink',
        inputs=rule.real,
        variables={'input': rule.link}
    )
