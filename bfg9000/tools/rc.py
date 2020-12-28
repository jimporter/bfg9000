import re

from . import builder, cc, msvc
from .. import log, shell
from .common import choose_builder, guess_command, make_command_converter
from ..languages import known_langs

with known_langs.make('rc') as x:
    x.vars(compiler='RC', flags='RCFLAGS')
    x.exts(source=['.rc'])

_c_to_rc = make_command_converter([
    (re.compile(r'gcc(?:-[\d.]+)?(?:-(?:posix|win32))?'), 'windres'),
])

_posix_cmds = ['windres']
_windows_cmds = ['rc', 'windres']
_builders = (cc.CcRcBuilder, msvc.MsvcRcBuilder)


@builder('rc')
def rc_builder(env):
    langinfo = known_langs['rc']
    cmd = env.getvar(langinfo.var('compiler'))
    if cmd:
        return choose_builder(env, langinfo, _builders, candidates=cmd)

    # We don't have an explicitly-set command from the environment, so try to
    # guess what the right command would be based on the C compiler command.
    candidates = (_windows_cmds if env.host_platform.family == 'windows'
                  else _posix_cmds)
    sibling = env.builder('c').compiler
    guessed_cmd = guess_command(sibling, _c_to_rc)

    # If the guessed command is the same as the first default command
    # candidate, remove it. This will keep us from logging a useless info
    # message that we guessed the default value for the command.
    if guessed_cmd is not None and guessed_cmd != candidates[0]:
        try:
            builder = choose_builder(env, langinfo, _builders,
                                     candidates=guessed_cmd, strict=True)
            log.info('guessed windows rc compiler {!r} from c compiler {!r}'
                     .format(guessed_cmd, shell.join(sibling.command)))
            return builder
        except IOError:
            pass

    # Try the default command candidates.
    return choose_builder(env, langinfo, _builders,
                          candidates=candidates)
