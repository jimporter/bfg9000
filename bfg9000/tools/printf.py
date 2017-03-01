from . import tool
from .utils import SimpleCommand
from ..iterutils import iterate
from ..safe_str import shell_literal
from ..shell import shell_list


@tool('printf')
class Printf(SimpleCommand):
    rule_name = command_var = 'printf'

    def __init__(self, env):
        default = ['printf', env.bfgdir.append('bfg9000-printf')]
        SimpleCommand.__init__(self, env, 'PRINTF', default)

    def _call(self, cmd, format, input, output):
        result = shell_list([cmd, format])
        result.extend(iterate(input))
        result.extend([shell_literal('>'), output])
        return result
