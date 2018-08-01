from . import builder, cc
from .common import choose_builder
from .. import shell
from ..iterutils import first
from ..languages import language, lang2cmd, lang2flags

language('f77', cmd_var='FC', flags_var='FFLAGS',
         src_exts=['.f', '.for', '.ftn'])
language('f95', cmd_var='FC', flags_var='FFLAGS',
         src_exts=['.f90', '.f95', '.f03', '.f08'])

_default_cmds = ['gfortran']
_builders = (cc.CcBuilder,)


@builder('f77', 'f95')
def fortran_builder(env, lang):
    var, flags_var = lang2cmd[lang], lang2flags[lang]
    candidates = env.getvar(var, _default_cmds)

    flags = (
        shell.split(env.getvar('CPPFLAGS', '')) +
        shell.split(env.getvar(flags_var, ''))
    )
    return choose_builder(env, lang, candidates, _builders, var.lower(),
                          flags_var.lower(), flags)
