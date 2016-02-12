from collections import namedtuple

ArgumentInfo = namedtuple('ArgumentInfo', ['name', 'type'])

# This is an extremely simplistic argument parser designed to understand
# arguments formatted for Visual Studio tools. It's used to parse user
# arguments so they can be correctly inserted into MSBuild files.


class ArgumentParser(object):
    def __init__(self, prefix_chars='/-', value_delim=':'):
        self.prefix_chars = prefix_chars
        self.value_delim = value_delim
        self._options = []
        self._short_names = {}
        self._long_names = {}

    def add(self, *args, **kwargs):
        info = ArgumentInfo(kwargs.get('dest', args[0][1:]),
                            kwargs.get('type', bool))
        self._options.append(info)

        for i in args:
            if i[0] not in self.prefix_chars:
                raise ValueError('names must begin with a prefix char')
            if len(i) == 2:
                self._short_names[i] = info
            else:
                self._long_names[i] = info

    def parse_known(self, args):
        result = {i.name: i.type() for i in self._options}
        extra = []

        def fill_value(info, value):
            if not value:
                raise ValueError('expected value for option')
            if info.type == list:
                result[info.name].append(value)
            else:
                result[info.name] = value

        args = iter(args)
        while True:
            i = next(args, None)
            if i is None:
                break

            if i[0] in self.prefix_chars:
                short_name, value = i[:2], i[2:]
                if short_name in self._short_names:
                    info = self._short_names[short_name]
                    if info.type == bool:
                        if value:
                            raise ValueError('no value expected for option')
                        value = True
                    elif len(i) == 2:
                        value = next(args)

                    fill_value(info, value)
                    continue

                long_name, colon, value = i.partition(self.value_delim)
                if long_name in self._long_names:
                    info = self._long_names[long_name]
                    if info.type == bool:
                        if colon:
                            raise ValueError('no value expected for option')
                        value = True

                    fill_value(info, value)
                    continue

            extra.append(i)

        return result, extra
