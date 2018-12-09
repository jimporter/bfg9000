from . import builder, cc
from .common import choose_builder
from ..languages import known_langs

with known_langs.make('f77') as x:
    x.vars(compiler='FC', flags='FFLAGS')
    x.exts(source=['.f', '.for', '.ftn'])

with known_langs.make('f95') as x:
    x.vars(compiler='FC', flags='FFLAGS')
    x.exts(source=['.f90', '.f95', '.f03', '.f08'])

_default_cmds = ['gfortran']
_builders = (cc.CcBuilder,)


@builder('f77', 'f95')
def fortran_builder(env, lang):
    return choose_builder(env, known_langs[lang], _default_cmds, _builders)
