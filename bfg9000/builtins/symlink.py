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
    symlink = env.tool('symlink')
    recipename = make.var('RULE_{}'.format(symlink.rule_name.upper()))
    if not buildfile.has_variable(recipename):
        buildfile.define(recipename, [symlink(make.var('1'), make.qvar('@'))])

    buildfile.rule(
        target=rule.output,
        deps=rule.real,
        recipe=make.Call(recipename, rule.link)
    )


@ninja.rule_handler(Symlink)
def ninja_symlink(rule, build_inputs, buildfile, env):
    symlink = env.tool('symlink')
    if not buildfile.has_rule(symlink.rule_name):
        buildfile.rule(
            name=symlink.rule_name,
            command=symlink(ninja.var('input'), output=ninja.var('out'))
        )

    buildfile.build(
        output=rule.output,
        rule=symlink.rule_name,
        inputs=rule.real,
        variables={'input': rule.link}
    )
