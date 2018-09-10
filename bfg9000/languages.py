from functools import partial
from six import iteritems

from .iterutils import listify, iterate


class _LanguageInfo(object):
    def __init__(self, name, vars, exts):
        self.name = name
        self._vars = vars
        self._exts = {k: listify(v) for k, v in iteritems(exts)}

    def _get(self, attr, desc, key):
        try:
            return getattr(self, attr)[key]
        except KeyError:
            raise ValueError('language {!r} does not support {} {!r}'
                             .format(self.name, desc, key))

    def var(self, name):
        return self._get('_vars', 'var', name)

    def exts(self, name):
        return self._get('_exts', 'file type', name)


class _LanguageDefiner(object):
    def __init__(self, langs, name):
        self._langs = langs
        self._name = name
        self._vars = {}
        self._exts = {}

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self._langs._add(_LanguageInfo(
            self._name, self._vars, self._exts
        ))

    def vars(self, **kwargs):
        self._vars = kwargs

    def exts(self, **kwargs):
        self._exts = kwargs


class Languages(object):
    def __init__(self):
        self._langs = {}
        self._ext2lang = {}

    def __getitem__(self, name):
        try:
            return self._langs[name]
        except KeyError:
            raise ValueError('unrecognized language {!r}'.format(name))

    def _add(self, info):
        self._langs[info.name] = info
        for kind, exts in iteritems(info._exts):
            for ext in exts:
                tolang = self._ext2lang.setdefault(ext, {})
                if kind in tolang:
                    raise ValueError('{ext!r} already used by {lang!r}'.format(
                        ext=ext, lang=tolang[kind]
                    ))
                tolang[kind] = info.name

    def fromext(self, ext, kind):
        return self._ext2lang.get(ext, {}).get(kind)

    def make(self, name):
        return _LanguageDefiner(self, name)


known_langs = Languages()
