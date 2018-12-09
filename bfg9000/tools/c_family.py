from . import builder, cc, msvc
from .common import choose_builder
from ..languages import known_formats, known_langs

with known_langs.make('c') as x:
    x.vars(compiler='CC', flags='CFLAGS')
    x.exts(source=['.c'], header=['.h'])

with known_langs.make('c++') as x:
    x.vars(compiler='CXX', flags='CXXFLAGS')
    x.exts(source=['.cpp', '.cc', '.cp', '.cxx', '.CPP', '.c++', '.C'],
           header=['.hpp', '.hh', '.hp', '.hxx', '.HPP', '.h++', '.H'])

with known_langs.make('objc') as x:
    x.vars(compiler='OBJC', flags='OBJCFLAGS')
    x.exts(source=['.m'])

with known_langs.make('objc++') as x:
    x.vars(compiler='OBJCXX', flags='OBJCXXFLAGS')
    x.exts(source=['.mm', '.M'])

with known_formats.make('native', mode='dynamic') as x:
    x.vars(linker='LD', flags='LDFLAGS', libs='LDLIBS')
with known_formats.make('native', mode='static') as x:
    x.vars(linker='AR', flags='ARFLAGS')

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
    cmd_map = (_windows_cmds if env.host_platform.family == 'windows'
               else _posix_cmds)
    return choose_builder(env, known_langs[lang], cmd_map[lang], _builders)
