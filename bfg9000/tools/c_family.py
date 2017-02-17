import os.path
import re

from . import builder, cc, msvc
from .. import shell
from .utils import check_which
from ..languages import language

language('c', src_exts=['.c'], hdr_exts=['.h'])
language('c++', src_exts=['.cpp', '.cc', '.cp', '.cxx', '.CPP', '.c++', '.C'],
         hdr_exts=['.hpp'])
language('objc', src_exts=['.m'])
language('objc++', src_exts=['.mm', '.M'])

_vars = {
    'c'     : ('CC'    , 'CFLAGS'     ),
    'c++'   : ('CXX'   , 'CXXFLAGS'   ),
    'objc'  : ('OBJC'  , 'OBJCFLAGS'  ),
    'objc++': ('OBJCXX', 'OBJCXXFLAGS'),
}
_posix_cmds = {
    'c'     : 'cc' ,
    'c++'   : 'c++',
    'objc'  : 'cc' ,
    'objc++': 'c++',
}
_windows_cmds = {
    'c'     : ['cl', 'clang-cl', 'cc', 'gcc', 'clang'],
    'c++'   : ['cl', 'clang-cl', 'c++', 'g++', 'clang++'],
    'objc'  : ['cc', 'gcc', 'clang'],
    'objc++': ['c++', 'g++', 'clang++'],
}


@builder('c', 'c++', 'objc', 'objc++')
def c_family_builder(env, lang):
    var, flags_var = _vars[lang]
    low_var, low_flags_var = var.lower(), flags_var.lower()

    if env.platform.name == 'windows':
        default_cmds = _windows_cmds
    else:
        default_cmds = _posix_cmds
    cmd = env.getvar(var, default_cmds[lang])
    cmd = check_which(cmd, kind='{} compiler'.format(lang))

    cflags = (
        shell.split(env.getvar(flags_var, '')) +
        shell.split(env.getvar('CPPFLAGS', ''))
    )
    ldflags = shell.split(env.getvar('LDFLAGS', ''))
    ldlibs = shell.split(env.getvar('LDLIBS', ''))

    # XXX: It might make more sense to try to check version strings instead of
    # filenames, but the command-line arg for version info can't be determined
    # ahead of time.
    if re.search(r'cl(-\d+\.\d+)?(\.exe)?($|\s)', cmd):
        origin = os.path.dirname(cmd)
        link_cmd = env.getvar('VCLINK', os.path.join(origin, 'link'))
        lib_cmd = env.getvar('VCLIB', os.path.join(origin, 'lib'))
        check_which(link_cmd, kind='dynamic linker'.format(lang))
        check_which(lib_cmd, kind='static linker'.format(lang))

        return msvc.MsvcBuilder(env, lang, low_var, cmd, link_cmd, lib_cmd,
                                low_flags_var, cflags, ldflags, ldlibs)
    else:
        return cc.CcBuilder(env, lang, low_var, cmd, low_flags_var, cflags,
                            ldflags, ldlibs)
