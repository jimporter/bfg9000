import re

from . import builder, cc, msvc
from .common import choose_builder
from .. import shell
from ..languages import language_vars, language_exts, lang2var


language_vars('c', compiler='CC', cflags='CFLAGS')
language_exts('c', source=['.c'], header='.h')

language_vars('c++', compiler='CXX', cflags='CXXFLAGS')
language_exts('c++',
              source=['.cpp', '.cc', '.cp', '.cxx', '.CPP', '.c++', '.C'],
              header=['.hpp', '.hh', '.hp', '.hxx', '.HPP', '.h++', '.H'])

language_vars('objc', compiler='OBJC', cflags='OBJCFLAGS')
language_exts('objc', source=['.m'])

language_vars('objc++', compiler='OBJCXX', cflags='OBJCXXFLAGS')
language_exts('objc++', source=['.mm', '.M'])

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
    var, flags_var = lang2var('compiler', lang), lang2var('cflags', lang)
    cmd_map = (_windows_cmds if env.host_platform.name == 'windows'
               else _posix_cmds)
    candidates = env.getvar(var, cmd_map[lang])

    flags = (
        shell.split(env.getvar('CPPFLAGS', '')) +
        shell.split(env.getvar(flags_var, ''))
    )
    return choose_builder(env, lang, candidates, _builders, var.lower(),
                          flags_var.lower(), flags)
