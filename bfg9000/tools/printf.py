from . import tool
from .utils import SimpleCommand
from ..iterutils import iterate
from ..safe_str import escaped_str
from ..shell import shell_list


@tool('printf')
class Printf(SimpleCommand):
    rule_name = command_var = 'printf'

    def __init__(self, env):
        default = ['printf', env.bfgdir.append('bfg9000-printf')]
        SimpleCommand.__init__(self, env, 'PRINTF', default)

    def __call__(self, cmd, format, input, output):
        result = shell_list([cmd, format])
        result.extend(iterate(input))
        result.extend([escaped_str('>'), output])
        return result
