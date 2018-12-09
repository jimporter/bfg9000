from six import iteritems

from .iterutils import listify


class _Info(object):
    def __init__(self, name, kind, vars, exts=None):
        self.name = name
        self._kind = kind
        self._var = vars
        if exts is not None:
            self._exts = {k: listify(v) for k, v in iteritems(exts)}

    def __getattr__(self, attr):
        if not hasattr(self, '_' + attr):
            raise AttributeError(attr)

        def inner(key):
            try:
                return getattr(self, '_' + attr)[key]
            except KeyError:
                desc = 'file type' if attr == 'exts' else attr
                raise ValueError('{} {!r} does not support {} {!r}'
                                 .format(self._kind, self.name, desc, key))
        return inner


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
        return _Definer(self, name, kind='language', fields=['vars', 'exts'])


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
