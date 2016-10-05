from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import Edge
from ..iterutils import listify


class WriteFile(Edge):
    def __init__(self, build, output, text):
        self.text = listify(text)
        Edge.__init__(self, build, output)


@make.rule_handler(WriteFile)
def make_write_file(rule, build_inputs, buildfile, env):
    printf = env.tool('printf')
    recipename = make.var('RULE_{}'.format(printf.rule_name.upper()))
    if not buildfile.has_variable(recipename):
        buildfile.define(recipename, [printf(
            cmd=make.cmd_var(printf, buildfile), format='%s\\n',
            input=make.var('1'), output=make.qvar('@')
        )])

    buildfile.rule(
        target=rule.output,
        recipe=make.Call(recipename, rule.text)
    )


@ninja.rule_handler(WriteFile)
def ninja_write_file(rule, build_inputs, buildfile, env):
    printf = env.tool('printf')
    if not buildfile.has_rule(printf.rule_name):
        buildfile.rule(
            name=printf.rule_name,
            command=[printf(
                cmd=ninja.cmd_var(printf, buildfile), format='%s\\n',
                input=ninja.var('text'), output=ninja.var('out')
            )]
        )

    buildfile.build(
        output=rule.output,
        rule=printf.rule_name,
        variables={'text': rule.text}
    )

try:
    from ..backends.msbuild import writer as msbuild

    @msbuild.rule_handler(WriteFile)
    def msbuild_write_file(rule, build_inputs, solution, env):
        printf = env.tool('printf')
        output = rule.output[0]
        project = msbuild.ExecProject(
            env, name=output.path.suffix,
            commands=[printf(printf.command, '%s\\n', rule.text, output.path)],
            dependencies=solution.dependencies(rule.extra_deps),
        )
        solution[output] = project
except:
    pass
