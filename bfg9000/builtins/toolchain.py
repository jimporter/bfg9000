import os
from six import iteritems

from . import builtin
from .. import shell
from .. import tools
from ..iterutils import isiterable
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
def which(names, resolve=False):
    return ' '.join(shell.which(names, resolve=resolve))


@builtin.function(context='toolchain')
def compiler(names, lang):
    var = known_langs[lang].var('compiler')
    os.environ[var] = ' '.join(shell.which(names))


@builtin.function(context='toolchain')
def compile_options(options, lang):
    # This only supports string (and lists of strings) for options, *not*
    # semantic options. It would be nice if we could support semantic options,
    # but we'd either need to know the flavor of compiler at this point (we
    # don't) or we'd have to store the options in some way other than as an
    # environment variable.
    if isiterable(options):
        options = pshell.join(options)
    os.environ[known_langs[lang].var('cflags')] = options


@builtin.function(context='toolchain')
def runner(names, lang):
    var = known_langs[lang].var('runner')
    os.environ[var] = ' '.join(shell.which(names))
