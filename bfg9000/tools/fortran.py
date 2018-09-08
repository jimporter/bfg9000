from . import builder, cc
from .common import choose_builder
from .. import shell
from ..iterutils import first
from ..languages import language_vars, language_exts, lang2var

language_vars('f77', compiler='FC', cflags='FFLAGS')
language_exts('f77', source=['.f', '.for', '.ftn'])

language_vars('f95', compiler='FC', cflags='FFLAGS')
language_exts('f95', source=['.f90', '.f95', '.f03', '.f08'])

_default_cmds = ['gfortran']
_builders = (cc.CcBuilder,)


@builder('f77', 'f95')
def fortran_builder(env, lang):
    var, flags_var = lang2var('compiler', lang), lang2var('cflags', lang)
    candidates = env.getvar(var, _default_cmds)

    flags = (
        shell.split(env.getvar('CPPFLAGS', '')) +
        shell.split(env.getvar(flags_var, ''))
    )
    return choose_builder(env, lang, candidates, _builders, var.lower(),
                          flags_var.lower(), flags)
