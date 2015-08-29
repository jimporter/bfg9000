import re

def _library_macro(name, suffix):
    return '{name}_{suffix}'.format(
        name=re.sub(r'\W', '_', name.upper()), suffix=suffix
    )

def shared_library_macro(name):
    return _library_macro(name, 'EXPORTS')

def static_library_macro(name):
    return _library_macro(name, 'STATIC')
