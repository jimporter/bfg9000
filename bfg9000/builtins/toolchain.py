import os
from six import iteritems

from . import builtin
from .. import shell

_unsafe_builtins = ['file', '__import__', 'input', 'open', 'raw_input',
                    'reload']


@builtin.getter(context='toolchain')
def environ():
    return os.environ


@builtin.function('toolchain', context='toolchain')
def target_platform(toolchain, platform):
    toolchain.target_platform = platform


@builtin.getter(name='__builtins__', context='toolchain')
def builtins():
    return {k: v for k, v in iteritems(__builtins__)
            if k not in _unsafe_builtins}


@builtin.function(context='toolchain')
def which(names, resolve=False):
    return ' '.join(shell.which(names, resolve=resolve))
