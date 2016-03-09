from . import ar, cc
from .. import shell
from .hooks import builder
from .utils import check_which
from ..languages import language

language('f77', exts=['.f', '.for', '.ftn'])
language('f95', exts=['.f90', '.f95', '.f03', '.f08'])


@builder('f77', 'f95')
class FortranBuilder(object):
    default_cmds = ['gfortran']

    def __init__(self, env, lang):
        cmd = env.getvar('FC', self.default_cmds)
        cmd = check_which(cmd, kind='{} compiler'.format(lang))

        cflags = shell.split(env.getvar('FFLAGS', ''))
        ldflags = shell.split(env.getvar('LDFLAGS', ''))
        ldlibs = shell.split(env.getvar('LDLIBS', ''))

        self.compiler = cc.CcCompiler(env, lang, 'fc', cmd, cflags)
        self.linkers = {
            'executable': cc.CcExecutableLinker(
                env, lang, 'fc', cmd, ldflags, ldlibs
            ),
            'shared_library': cc.CcSharedLibraryLinker(
                env, lang, 'fc', cmd, ldflags, ldlibs
            ),
            'static_library': ar.ArLinker(env, lang),
        }
        self.packages = cc.CcPackageResolver(env, lang, cmd)
