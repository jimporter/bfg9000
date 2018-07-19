# This is an extremely simplistic argument parser designed to understand
# arguments formatted for Visual Studio tools. It's used to parse user
# arguments so they can be correctly inserted into MSBuild files.


class ArgumentParser(object):
    _argument_info = {}

    def __init__(self, prefix_chars='/-', value_delim=':'):
        self.prefix_chars = prefix_chars
        self.value_delim = value_delim
        self._options = []
        self._short_names = {}
        self._long_names = {}
        self._unnamed_dest = None

    @classmethod
    def handler(cls, type):
        def wrapper(thing):
            cls._argument_info[type] = thing
            return thing
        return wrapper

    def add(self, *args, **kwargs):
        dest = kwargs.pop('dest', args[0][1:])
        type = kwargs.pop('type', bool)
        info = self._argument_info[type](dest, **kwargs)

        for i in args:
            if i[0] not in self.prefix_chars:
                raise ValueError('names must begin with a prefix char')
            if len(i) == 2:
                self._short_names[i] = info
            else:
                self._long_names[i] = info

        self._options.append(info)
        return info

    def add_unnamed(self, dest):
        self._unnamed_dest = dest

    def parse_known(self, args):
        result = {i.name: i.default() for i in self._options}
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
                            value = next(args)
                    elif value:
                        raise ValueError('no value expected for option')
                else:
                    key, colon, value = i.partition(self.value_delim)
                    if key in self._long_names:
                        info = self._long_names[key]
                        if not info.takes_value and colon:
                            raise ValueError('no value expected for option')
            elif self._unnamed_dest:
                result[self._unnamed_dest].append(i)
                continue

            if info:
                info.fill_value(result, key, value)
                continue
            extra.append(i)

        return result, extra


class ArgumentInfo(object):
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


@ArgumentParser.handler(bool)
class BoolArgumentInfo(ArgumentInfo):
    def __init__(self, name, value=True):
        ArgumentInfo.__init__(self, name)
        self.value = value

    def fill_value(self, results, key, value):
        results[self.name] = self.value

    @property
    def takes_value(self):
        return False


@ArgumentParser.handler(str)
class StrArgumentInfo(ArgumentInfo):
    def __init__(self, name):
        ArgumentInfo.__init__(self, name)

    def fill_value(self, results, key, value):
        if not value:
            raise ValueError('expected value for option')
        results[self.name] = value


@ArgumentParser.handler(list)
class ListArgumentInfo(ArgumentInfo):
    def __init__(self, name):
        ArgumentInfo.__init__(self, name)

    def default(self):
        return []

    def fill_value(self, results, key, value):
        if not value:
            raise ValueError('expected value for option')
        results[self.name].append(value)


@ArgumentParser.handler(dict)
class DictArgumentInfo(ArgumentInfo):
    def __init__(self, name):
        ArgumentInfo.__init__(self, name)
        self._short_names = {}
        self._long_names = {}
        self._options = []

    def add(self, *args, **kwargs):
        dest = kwargs.pop('dest', args[0])
        type = kwargs.pop('type', 'key')
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
        if not value:
            raise ValueError('expected value for option')

        subkey, subvalue = value[:1], value[1:]
        if subkey in self._short_names:
            info = self._short_names[subkey]
            info.fill_value(results[self.name], subkey, subvalue)
        elif value in self._long_names:
            info = self._long_names[value]
            info.fill_value(results[self.name], value, None)
