import re

from . import builder, cc, msvc
from .common import choose_builder
from .. import shell
from ..languages import known_langs

with known_langs.make('c') as x:
    x.vars(compiler='CC', cflags='CFLAGS')
    x.exts(source=['.c'], header=['.h'])

with known_langs.make('c++') as x:
    x.vars(compiler='CXX', cflags='CXXFLAGS')
    x.exts(source=['.cpp', '.cc', '.cp', '.cxx', '.CPP', '.c++', '.C'],
           header=['.hpp', '.hh', '.hp', '.hxx', '.HPP', '.h++', '.H'])

with known_langs.make('objc') as x:
    x.vars(compiler='OBJC', cflags='OBJCFLAGS')
    x.exts(source=['.m'])

with known_langs.make('objc++') as x:
    x.vars(compiler='OBJCXX', cflags='OBJCXXFLAGS')
    x.exts(source=['.mm', '.M'])

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
    cmd_map = (_windows_cmds if env.host_platform.name == 'windows'
               else _posix_cmds)
    return choose_builder(env, known_langs[lang], cmd_map[lang], _builders)
