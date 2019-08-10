from itertools import chain
from six import iteritems, iterkeys

from .iterutils import listify


class _Info(object):
    def __init__(self, name, kind, vars, exts=None, auxexts={}):
        self.name = name
        self._kind = kind
        self._var = vars

        if exts is not None:
            allkeys = set(iterkeys(exts)) | set(iterkeys(auxexts))
            self._exts = {i: listify(exts.get(i)) for i in allkeys}
            self._auxexts = {i: listify(auxexts.get(i)) for i in allkeys}

    def __get_prop(attr, desc):
        def inner(self, key):
            try:
                return getattr(self, attr)[key]
            except KeyError:
                raise ValueError('{} {!r} does not support {} {!r}'
                                 .format(self._kind, self.name, desc, key))
        return inner

    var = __get_prop('_var', 'var')
    exts = __get_prop('_exts', 'file type')
    auxexts = __get_prop('_auxexts', 'file type')

    def allexts(self, key):
        return self.exts(key) + self.auxexts(key)

    def default_ext(self, key):
        exts = self.exts(key)
        if len(exts):
            return exts[0]
        return self.auxexts(key)[0]

    def extkind(self, ext):
        for k, v in chain(iteritems(self._exts), iteritems(self._auxexts)):
            if ext in v:
                return k
        return None


class _Definer(object):
    def __init__(self, parent, name, kind, fields):
        self._parent = parent
        self._name = name
        self._kind = kind
        self._fields = {i: {} for i in fields}

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self._parent._add(_Info(self._name, self._kind, **self._fields))

    def __getattr__(self, attr):
        if attr not in self._fields:
            raise AttributeError(attr)

        def inner(**kwargs):
            self._fields[attr] = kwargs

        return inner


class Languages(object):
    def __init__(self):
        self._langs = {}
        self._ext2lang = {}

    def __getitem__(self, name):
        try:
            return self._langs[name]
        except KeyError:
            raise ValueError('unrecognized language {!r}'.format(name))

    def __contains__(self, name):
        return name in self._langs

    def _add(self, info):
        self._langs[info.name] = info
        for kind, exts in iteritems(info._exts):
            for ext in exts:
                if ext in self._ext2lang:
                    raise ValueError('{ext!r} already used by {lang!r}'.format(
                        ext=ext, lang=self._ext2lang[ext][0]
                    ))
                self._ext2lang[ext] = (info.name, kind)

    def fromext(self, ext, kind):
        lang, langkind = self.extinfo(ext)
        return lang if langkind == kind else None

    def extinfo(self, ext):
        return self._ext2lang.get(ext, (None, None))

    def make(self, name):
        return _Definer(self, name, kind='language',
                        fields=['vars', 'exts', 'auxexts'])


class Formats(object):
    def __init__(self):
        self._formats = {}

    def __getitem__(self, name):
        try:
            return self._formats[name[0]][name[1]]
        except KeyError:
            raise ValueError('unrecognized format {!r}'.format(name))

    def _add(self, info):
        name, mode = info.name
        if name not in self._formats:
            self._formats[name] = {}
        self._formats[name][mode] = info

    def make(self, name, mode):
        return _Definer(self, (name, mode), kind='format', fields=['vars'])


known_langs = Languages()
known_formats = Formats()
