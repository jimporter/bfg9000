from . import cc
from .. import shell
from .hooks import builder
from .utils import check_which
from ..languages import language

language('f77', src_exts=['.f', '.for', '.ftn'])
language('f95', src_exts=['.f90', '.f95', '.f03', '.f08'])

_default_cmds = ['gfortran']


@builder('f77', 'f95')
def fortran_builder(env, lang):
    cmd = env.getvar('FC', _default_cmds)
    cmd = check_which(cmd, kind='{} compiler'.format(lang))

    cflags = shell.split(env.getvar('FFLAGS', ''))
    ldflags = shell.split(env.getvar('LDFLAGS', ''))
    ldlibs = shell.split(env.getvar('LDLIBS', ''))

    return cc.CcBuilder(env, lang, 'fc', cmd, cflags, ldflags, ldlibs)
