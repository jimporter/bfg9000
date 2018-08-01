import re

from . import builder, cc, msvc
from .common import choose_builder
from .. import shell
from ..languages import language, lang2cmd, lang2flags

language('c', cmd_var='CC', flags_var='CFLAGS',
         src_exts=['.c'], hdr_exts=['.h'])
language('c++', cmd_var='CXX', flags_var='CXXFLAGS',
         src_exts=['.cpp', '.cc', '.cp', '.cxx', '.CPP', '.c++', '.C'],
         hdr_exts=['.hpp', '.hh', '.hp', '.hxx', '.HPP', '.h++', '.H'])
language('objc', cmd_var='OBJC', flags_var='OBJCFLAGS', src_exts=['.m'])
language('objc++', cmd_var='OBJCXX', flags_var='OBJCXXFLAGS',
         src_exts=['.mm', '.M'])

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
    var, flags_var = lang2cmd[lang], lang2flags[lang]
    cmd_map = (_windows_cmds if env.host_platform.name == 'windows'
               else _posix_cmds)
    candidates = env.getvar(var, cmd_map[lang])

    flags = (
        shell.split(env.getvar('CPPFLAGS', '')) +
        shell.split(env.getvar(flags_var, ''))
    )
    return choose_builder(env, lang, candidates, _builders, var.lower(),
                          flags_var.lower(), flags)
