import os
from six import iteritems

from . import builtin
from .. import shell
from .. import tools
from ..iterutils import first, isiterable
from ..languages import known_langs
from ..shell import posix as pshell

_unsafe_builtins = ['file', '__import__', 'input', 'open', 'raw_input',
                    'reload']


@builtin.getter(name='__builtins__', context='toolchain')
def builtins():
    return {k: v for k, v in iteritems(__builtins__)
            if k not in _unsafe_builtins}


@builtin.getter(context='toolchain')
def environ():
    return os.environ


@builtin.function('toolchain', context='toolchain')
def target_platform(toolchain, platform):
    toolchain.target_platform = platform


@builtin.function(context='toolchain')
def which(names, resolve=False, strict=True, kind='executable'):
    try:
        return ' '.join(shell.which(names, resolve=resolve, kind=kind))
    except IOError:
        if strict:
            raise
        result = first(names)
        return pshell.join(result) if isiterable(result) else result


@builtin.function(context='toolchain')
def compiler(names, lang, strict=False):
    var = known_langs[lang].var('compiler')
    os.environ[var] = which(names, strict=strict, kind='compiler')


@builtin.function(context='toolchain')
def compile_options(options, lang):
    # This only supports strings (and lists of strings) for options, *not*
    # semantic options. It would be nice if we could support semantic options,
    # but we'd either need to know the flavor of compiler at this point (we
    # don't) or we'd have to store the options in some way other than as an
    # environment variable.
    if isiterable(options):
        options = pshell.join(options)
    os.environ[known_langs[lang].var('flags')] = options


@builtin.function(context='toolchain')
def runner(names, lang, strict=False):
    var = known_langs[lang].var('runner')
    os.environ[var] = which(names, strict=strict, kind='runner')
