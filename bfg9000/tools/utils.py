import re

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
