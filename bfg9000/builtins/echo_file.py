from .. import shell
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import Edge


class EchoFile(Edge):
    def __init__(self, build, output, text):
        self.text = text
        Edge.__init__(self, build, output)


@make.rule_handler(EchoFile)
def make_echo_file(rule, build_inputs, buildfile, env):
    recipename = make.var('ECHO_FILE')
    if not buildfile.has_variable(recipename):
        buildfile.define(recipename, [
            'echo ' + make.var('1') + ' > ' + make.qvar('@'),
        ])

    buildfile.rule(
        target=rule.output,
        recipe=make.Call(recipename, rule.text)
    )


@ninja.rule_handler(EchoFile)
def ninja_echo_file(rule, build_inputs, buildfile, env):
    if not buildfile.has_rule('echo_file'):
        buildfile.rule(
            name='echo_file',
            command=ninja.Commands(
                'echo ' + ninja.var('text') + ' > ' + ninja.var('out')
            )
        )

    text = (rule.text if env.platform.name == 'windows'
            else shell.quote(rule.text))
    buildfile.build(
        output=rule.output,
        rule='echo_file',
        variables={'text': text}
    )

try:
    from ..backends.msbuild import writer as msbuild

    @msbuild.rule_handler(EchoFile)
    def msbuild_echo_file(rule, build_inputs, solution, env):
        output = rule.output[0]
        project = msbuild.ExecProject(
            env, name=output.path.suffix,
            commands=['echo ' + rule.text + ' > ' + output.path],
            dependencies=solution.dependencies(rule.extra_deps),
        )
        solution[output] = project
except:
    pass
