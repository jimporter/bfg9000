import re

from . import builder, cc, msvc
from .. import shell
from .common import choose_builder
from ..languages import language

language('c', src_exts=['.c'], hdr_exts=['.h'])
language('c++',
         src_exts=['.cpp', '.cc', '.cp', '.cxx', '.CPP', '.c++', '.C'],
         hdr_exts=['.hpp', '.hh', '.hp', '.hxx', '.HPP', '.h++', '.H'])
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

_builders = (cc.CcBuilder, msvc.MsvcBuilder)


@builder('c', 'c++', 'objc', 'objc++')
def c_family_builder(env, lang):
    var, flags_var = _vars[lang]
    cmd_map = _windows_cmds if env.platform.name == 'windows' else _posix_cmds
    candidates = env.getvar(var, cmd_map[lang])

    flags = (
        shell.split(env.getvar('CPPFLAGS', '')) +
        shell.split(env.getvar(flags_var, ''))
    )
    return choose_builder(env, lang, candidates, _builders, var.lower(),
                          flags_var.lower(), flags)
