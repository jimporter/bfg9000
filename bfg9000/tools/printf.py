from .hooks import tool
from .utils import check_which
from ..iterutils import iterate
from ..safe_str import escaped_str
from ..shell import shell_list


@tool('printf')
class Printf(object):
    rule_name = command_var = 'printf'

    def __init__(self, env):
        command = env.getvar(
            'PRINTF', ['printf', env.bfgdir.append('bfg9000-printf')]
        )
        self.command = check_which(command)

    def __call__(self, cmd, format, input, output):
        result = shell_list([cmd, format])
        result.extend(iterate(input))
        result.extend([escaped_str('>'), output])
        return result
