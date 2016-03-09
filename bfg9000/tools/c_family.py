import os.path
import re

from . import ar, cc, msvc
from .. import shell
from .hooks import builder
from .utils import check_which
from ..languages import language

language('c', exts=['.c'])
language('c++', exts=['.cpp', '.cc', '.cp', '.cxx', '.CPP', '.c++', '.C'])
language('objc', exts=['.m'])
language('objc++', exts=['.mm', '.M'])


@builder('c', 'c++', 'objc', 'objc++')
class CFamilyBuilder(object):
    __vars = {
        'c'     : ('CC'    , 'CFLAGS'     ),
        'c++'   : ('CXX'   , 'CXXFLAGS'   ),
        'objc'  : ('OBJC'  , 'OBJCFLAGS'  ),
        'objc++': ('OBJCXX', 'OBJCXXFLAGS'),
    }
    __posix_cmds = {
        'c'     : 'cc' ,
        'c++'   : 'c++',
        'objc'  : 'cc' ,
        'objc++': 'c++',
    }
    __windows_cmds = {
        'c'     : ['cl', 'clang-cl', 'cc', 'gcc', 'clang'],
        'c++'   : ['cl', 'clang-cl', 'c++', 'g++', 'clang++'],
        'objc'  : ['cc', 'gcc', 'clang'],
        'objc++': ['c++', 'g++', 'clang++'],
    }

    def __init__(self, env, lang):
        var, flags_var = self.__vars[lang]
        low_var = var.lower()

        if env.platform.name == 'windows':
            default_cmds = self.__windows_cmds
        else:
            default_cmds = self.__posix_cmds
        cmd = env.getvar(var, default_cmds[lang])
        cmd = check_which(cmd, kind='{} compiler'.format(lang))

        cflags = (
            shell.split(env.getvar(flags_var, '')) +
            shell.split(env.getvar('CPPFLAGS', ''))
        )
        ldflags = shell.split(env.getvar('LDFLAGS', ''))
        ldlibs = shell.split(env.getvar('LDLIBS', ''))

        if re.match(r'\S*cl(\.exe)?($|\s)', cmd):
            origin = os.path.dirname(cmd)
            link_cmd = env.getvar(var + '_LINK', os.path.join(origin, 'link'))
            lib_cmd = env.getvar(var + '_LIB', os.path.join(origin, 'lib'))
            check_which(link_cmd, kind='{} linker'.format(lang))
            check_which(lib_cmd, kind='{} static linker'.format(lang))

            self.compiler = msvc.MsvcCompiler(env, lang, low_var, cmd, cflags)
            self.linkers = {
                'executable': msvc.MsvcExecutableLinker(
                    env, lang, low_var, link_cmd, ldflags, ldlibs
                ),
                'shared_library': msvc.MsvcSharedLibraryLinker(
                    env, lang, low_var, link_cmd, ldflags, ldlibs
                ),
                'static_library': msvc.MsvcStaticLinker(
                    env, lang, low_var, lib_cmd
                ),
            }
            self.packages = msvc.MsvcPackageResolver(env, lang)
        else:
            self.compiler = cc.CcCompiler(env, lang, low_var, cmd, cflags)
            self.linkers = {
                'executable': cc.CcExecutableLinker(
                    env, lang, low_var, cmd, ldflags, ldlibs
                ),
                'shared_library': cc.CcSharedLibraryLinker(
                    env, lang, low_var, cmd, ldflags, ldlibs
                ),
                'static_library': ar.ArLinker(env, lang),
            }
            self.packages = cc.CcPackageResolver(env, lang, cmd)
