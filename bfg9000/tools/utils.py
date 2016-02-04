import os
import re
import warnings
from six import string_types

from .. import shell
from ..path import Path
from ..platforms import which

_modes = {
    'shared_library': 'EXPORTS',
    'static_library': 'STATIC',
}


def library_macro(name, mode):
    # Since the name always begins with "lib", this always produces a valid
    # macro name.
    return '{name}_{suffix}'.format(
        name=re.sub(r'\W', '_', name.upper()), suffix=_modes[mode]
    )


def check_which(name, env=os.environ, kind='executable'):
    # Only check the first word, since some commands have built-in arguments,
    # like `mkdir -p`.
    if isinstance(name, string_types):
        name = shell.split(name)[0]
    elif isinstance(name, Path):
        name = name.string()

    try:
        which(name, env)
    except IOError:
        warnings.warn("unable to find {kind} '{name}'".format(
            kind=kind, name=name
        ))


def darwin_install_name(library):
    return os.path.join('@rpath', library.path.basename())
