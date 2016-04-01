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

    def parse_known(self, args):
        result = {i.name: i.default() for i in self._options}
        extra = []

        args = iter(args)
        while True:
            i = next(args, None)
            if i is None:
                break

            if i[0] in self.prefix_chars:
                short_name, value = i[:2], i[2:]
                if short_name in self._short_names:
                    info = self._short_names[short_name]
                    if info.takes_value:
                        if not value:
                            value = next(args)
                    elif value:
                        raise ValueError('no value expected for option')

                    info.fill_value(result, value)
                    continue

                long_name, colon, value = i.partition(self.value_delim)
                if long_name in self._long_names:
                    info = self._long_names[long_name]
                    if not info.takes_value and colon:
                        raise ValueError('no value expected for option')

                    info.fill_value(result, value)
                    continue

            extra.append(i)

        return result, extra


class ArgumentInfo(object):
    def __init__(self, name, type):
        self.name = name
        self.type = type

    def default(self):
        return None

    @property
    def takes_value(self):
        return True


@ArgumentParser.handler(bool)
class BoolArgumentInfo(ArgumentInfo):
    def __init__(self, name, value=True):
        ArgumentInfo.__init__(self, name, bool)
        self.value = value

    def fill_value(self, results, value=None):
        results[self.name] = self.value

    @property
    def takes_value(self):
        return False


@ArgumentParser.handler(str)
class StrArgumentInfo(ArgumentInfo):
    def __init__(self, name):
        ArgumentInfo.__init__(self, name, str)

    def fill_value(self, results, value):
        if not value:
            raise ValueError('expected value for option')
        results[self.name] = value


@ArgumentParser.handler(list)
class ListArgumentInfo(ArgumentInfo):
    def __init__(self, name):
        ArgumentInfo.__init__(self, name, list)

    def default(self):
        return []

    def fill_value(self, results, value):
        if not value:
            raise ValueError('expected value for option')
        results[self.name].append(value)
