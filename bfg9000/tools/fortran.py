from . import builder, cc
from .. import shell
from .common import choose_builder
from ..iterutils import first
from ..languages import language

language('f77', src_exts=['.f', '.for', '.ftn'])
language('f95', src_exts=['.f90', '.f95', '.f03', '.f08'])

_default_cmds = ['gfortran']
_builders = (cc.CcBuilder,)


@builder('f77', 'f95')
def fortran_builder(env, lang):
    candidates = env.getvar('FC', _default_cmds)

    flags = (
        shell.split(env.getvar('CPPFLAGS', '')) +
        shell.split(env.getvar('FFLAGS', ''))
    )
    return choose_builder(env, lang, candidates, _builders, 'fc', 'fflags',
                          flags)
