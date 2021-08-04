# This is an extremely simplistic argument parser designed to understand
# arguments formatted for Visual Studio tools. It's used to parse user
# arguments so they can be correctly inserted into MSBuild files.


class ArgumentParser:
    _argument_info = {}

    def __init__(self, prefix_chars='/-', value_delim=':',
                 case_sensitive=True):
        self.prefix_chars = prefix_chars
        self.value_delim = value_delim
        self.case_sensitive = case_sensitive
        self._options = []
        self._short_names = {}
        self._long_names = {}
        self._unnamed_dest = None

    def _normcase(self, s):
        return s if self.case_sensitive else s.lower()

    @classmethod
    def handler(cls, type):
        def wrapper(thing):
            cls._argument_info[type] = thing
            return thing
        return wrapper

    def add(self, *args, dest=None, type=bool, **kwargs):
        dest = dest or args[0][1:]
        info = self._argument_info[type](dest, **kwargs)

        for i in args:
            if i[0] not in self.prefix_chars:
                raise ValueError('names must begin with a prefix char')

            if len(i) == 2:
                if i in self._short_names:
                    raise ValueError('{!r} already defined'.format(i))
                self._short_names[i] = info
            else:
                if i[:2] in self._short_names:
                    raise ValueError('{!r} collides with {!r}'
                                     .format(i, i[:2]))

                i = self._normcase(i)
                if i in self._long_names:
                    raise ValueError('{!r} already defined'.format(i))
                self._long_names[i] = info

        self._options.append(info)
        return info

    def add_unnamed(self, dest):
        self._unnamed_dest = dest

    def parse_known(self, args):
        result = {i.name: i.default() for i in self._options if i.name}
        if self._unnamed_dest:
            result[self._unnamed_dest] = []
        extra = []

        args = iter(args)
        while True:
            i = next(args, None)
            if i is None:
                break

            info = None
            if i[0] in self.prefix_chars:
                key, value = i[:2], i[2:]
                if key in self._short_names:
                    info = self._short_names[key]
                    if info.takes_value:
                        if not value:
                            try:
                                value = next(args)
                            except StopIteration:
                                raise ValueError('expected value for option')
                    elif value:
                        raise ValueError('no value expected for option')
                else:
                    key, colon, value = i.partition(self.value_delim)
                    key = self._normcase(key)
                    if key in self._long_names:
                        info = self._long_names[key]
                        if not info.takes_value and colon:
                            raise ValueError('no value expected for option')
                        elif info.takes_value and not value:
                            raise ValueError('expected value for option')
            elif self._unnamed_dest:
                result[self._unnamed_dest].append(i)
                continue

            if info:
                if info.fill_value(result, key, value):
                    continue
            extra.append(i)

        return result, extra


class ArgumentInfo:
    def __init__(self, name):
        self.name = name

    def default(self):
        return None

    @property
    def takes_value(self):
        return True


@ArgumentParser.handler('key')
class KeyArgumentInfo(ArgumentInfo):
    def fill_value(self, results, key, value):
        results[self.name] = key
        return True


@ArgumentParser.handler('alias')
class AliasArgumentInfo(ArgumentInfo):
    def __init__(self, name, base, value=None):
        super().__init__(None)
        self.base = base
        self.value = value
        if self.value is not None and not self.base.takes_value:
            raise TypeError('base argument does not take a value')

    def fill_value(self, results, key, value):
        if self.value is not None:
            value = self.value
        self.base.fill_value(results, key, value)
        return True

    @property
    def takes_value(self):
        return self.value is None and self.base.takes_value


@ArgumentParser.handler(bool)
class BoolArgumentInfo(ArgumentInfo):
    def __init__(self, name, value=True):
        super().__init__(name)
        self.value = value

    def fill_value(self, results, key, value):
        results[self.name] = self.value
        return True

    @property
    def takes_value(self):
        return False


@ArgumentParser.handler(str)
class StrArgumentInfo(ArgumentInfo):
    def __init__(self, name):
        super().__init__(name)

    def fill_value(self, results, key, value):
        results[self.name] = value
        return True


@ArgumentParser.handler(list)
class ListArgumentInfo(ArgumentInfo):
    def __init__(self, name):
        super().__init__(name)

    def default(self):
        return []

    def fill_value(self, results, key, value):
        results[self.name].append(value)
        return True


@ArgumentParser.handler(dict)
class DictArgumentInfo(ArgumentInfo):
    def __init__(self, name, strict=False):
        super().__init__(name)
        self._short_names = {}
        self._long_names = {}
        self._options = []
        self._strict = strict

    def add(self, *args, dest=None, type='key', **kwargs):
        dest = dest or args[0]
        info = ArgumentParser._argument_info[type](dest, **kwargs)

        if type in (bool, 'key'):
            for i in args:
                self._long_names[i] = info
        else:
            for i in args:
                if len(i) != 1:
                    raise ValueError('short names should be one character')
                self._short_names[i] = info

        self._options.append(info)
        return info

    def default(self):
        return {i.name: i.default() for i in self._options}

    def fill_value(self, results, key, value):
        subkey, subvalue = value[:1], value[1:]
        if subkey in self._short_names:
            info = self._short_names[subkey]
            info.fill_value(results[self.name], subkey, subvalue)
            return True
        elif value in self._long_names:
            info = self._long_names[value]
            info.fill_value(results[self.name], value, None)
            return True
        elif self._strict:
            raise ValueError('unexpected value for option')

        return False
