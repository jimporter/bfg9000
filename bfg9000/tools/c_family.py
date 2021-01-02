from collections import namedtuple

from . import builder, cc, msvc
from .. import log
from .common import choose_builder, make_command_converter_pair
from ..languages import known_formats, known_langs

_guessed_info = namedtuple('_guessed_info', ['lang', 'cmd', 'guessed_cmd'])

with known_langs.make('c') as x:
    x.vars(compiler='CC', flags='CFLAGS')
    x.exts(source=['.c'], header=['.h'])

with known_langs.make('c++') as x:
    x.vars(compiler='CXX', flags='CXXFLAGS')
    x.exts(source=['.cpp', '.cc', '.cp', '.cxx', '.CPP', '.c++', '.C'],
           header=['.hpp', '.hh', '.hp', '.hxx', '.HPP', '.h++', '.H'])
    x.auxexts(header=['.h'])

with known_langs.make('objc') as x:
    x.vars(compiler='OBJC', flags='OBJCFLAGS')
    x.exts(source=['.m'])
    x.auxexts(header=['.h'])

with known_langs.make('objc++') as x:
    x.vars(compiler='OBJCXX', flags='OBJCXXFLAGS')
    x.exts(source=['.mm', '.M'])
    x.auxexts(header=['.h'])

with known_formats.make('native', src_lang='c') as fmt:
    with fmt.make('dynamic') as x:
        x.vars(linker='LD', flags='LDFLAGS', libs='LDLIBS')
    with fmt.make('static') as x:
        x.vars(linker='AR', flags='ARFLAGS')


_c_to_cxx, _cxx_to_c = make_command_converter_pair([
    # These are ordered from most- to least-specific; in particular, we want
    # `clang-cl` to stay that way when converted between C and C++ contexts.
    ('clang-cl', 'clang-cl'),
    ('cc', 'c++'),
    ('gcc', 'g++'),
    ('clang', 'clang++'),
    ('cl', 'cl'),
])

_siblings = {
    'c'     : ['objc', 'c++', 'objc++'],
    'c++'   : ['objc++', 'c', 'objc'],
    'objc'  : ['c', 'objc++', 'c++'],
    'objc++': ['c++', 'objc', 'c'],
}

_posix_cmds = {
    'c'     : ['cc'],
    'c++'   : ['c++'],
    'objc'  : ['cc'],
    'objc++': ['c++'],
}
_windows_cmds = {
    'c'     : ['cl', 'clang-cl', 'cc', 'gcc', 'clang'],
    'c++'   : ['cl', 'clang-cl', 'c++', 'g++', 'clang++'],
    'objc'  : ['cc', 'gcc', 'clang'],
    'objc++': ['c++', 'g++', 'clang++'],
}

_builders = (msvc.MsvcBuilder, cc.CcBuilder)
_fallback_posix_builder = cc.CcBuilder
_fallback_windows_builder = msvc.MsvcBuilder


def _guess_candidates(env, lang):
    def is_cxx_based(lang):
        return lang.endswith('c++')

    candidates = []
    cxx_based = is_cxx_based(lang)
    for i in _siblings[lang]:
        cmd = sibling_cmd = env.getvar(known_langs[i].var('compiler'))
        if sibling_cmd is not None:
            sibling_cxx_based = is_cxx_based(i)
            if cxx_based and not sibling_cxx_based:
                cmd = _c_to_cxx(cmd)
            elif not cxx_based and sibling_cxx_based:
                cmd = _cxx_to_c(cmd)
            if cmd is not None:
                candidates.append(_guessed_info(i, sibling_cmd, cmd))
    return candidates


@builder('c', 'c++', 'objc', 'objc++')
def c_family_builder(env, lang):
    if env.host_platform.family == 'windows':
        candidates = _windows_cmds[lang]
        fallback = _fallback_windows_builder
    else:
        candidates = _posix_cmds[lang]
        fallback = _fallback_posix_builder

    langinfo = known_langs[lang]
    cmd = env.getvar(langinfo.var('compiler'))
    if cmd:
        return choose_builder(env, langinfo, _builders, candidates=cmd,
                              fallback_builder=fallback)

    # We don't have an explicitly-set command from the environment, so try to
    # guess what the right command would be.
    guessed_info = _guess_candidates(env, lang)

    # If the last guessed command is the same as the first default command
    # candidate, remove it. This will keep us from logging a useless info
    # message that we guessed the default value for the command.
    if guessed_info and guessed_info[-1].guessed_cmd == candidates[0]:
        del guessed_info[-1]

    for sibling_lang, sibling_cmd, guessed_cmd in guessed_info:
        try:
            builder = choose_builder(env, langinfo, _builders,
                                     candidates=guessed_cmd,
                                     fallback_builder=fallback, strict=True)
            log.info('guessed {} compiler {!r} from {} compiler {!r}'.format(
                lang, guessed_cmd, sibling_lang, sibling_cmd
            ))
            return builder
        except IOError:
            pass

    # Try all the default command candidates we haven't already tried above.
    guesses = [i.guessed_cmd for i in guessed_info]
    untried_candidates = [i for i in candidates if i not in guesses]
    return choose_builder(env, langinfo, _builders,
                          candidates=untried_candidates,
                          fallback_builder=fallback)
