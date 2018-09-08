from functools import partial
from six import iteritems

from .iterutils import iterate

_lang2var = {}
_lang2ext = {}
_ext2lang = {}


def language_vars(lang, **kwargs):
    for kind, var in iteritems(kwargs):
        _lang2var.setdefault(lang, {})[kind] = var


def language_exts(lang, **kwargs):
    for kind, exts in iteritems(kwargs):
        _lang2ext.setdefault(lang, {}).setdefault(kind, []).extend(exts)

        for ext in iterate(exts):
            tolang = _ext2lang.setdefault(ext, {})
            if kind in tolang:
                raise ValueError('{ext!r} already used by {lang}'.format(
                    ext=ext, lang=lang
                ))
            tolang[kind] = lang


def _get(dct, desc, kind, thing, none_ok=False):
    if none_ok:
        return dct.get(thing, {}).get(kind)

    try:
        sub = dct[thing]
    except KeyError:
        raise ValueError('unrecognized {} {!r}'.format(desc, thing))
    return sub[kind]


lang2var = partial(_get, _lang2var, 'language')
lang2ext = partial(_get, _lang2ext, 'language')
ext2lang = partial(_get, _ext2lang, 'extension')
