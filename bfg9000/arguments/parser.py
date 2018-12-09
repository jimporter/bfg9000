import re as _re
from argparse import *

from .. import path as _path

_ArgumentParser = ArgumentParser


class ToggleAction(Action):
    def __init__(self, option_strings, dest, default=False, required=False,
                 help=None):
        self.true_strings = [self._prefix(i, self._true_prefix)
                             for i in option_strings]
        self.false_strings = [self._prefix(i, self._false_prefix)
                              for i in option_strings]

        option_strings = self.true_strings + self.false_strings
        Action.__init__(self, option_strings, dest=dest, nargs=0,
                        default=default, required=required, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        value = option_string in self.true_strings
        setattr(namespace, self.dest, value)

    @staticmethod
    def _prefix(s, prefix):
        if not s.startswith('--'):
            raise ValueError('option string must begin with "--"')
        return _re.sub('(^--(x-)?)', r'\1' + prefix, s)


class EnableAction(ToggleAction):
    _true_prefix = 'enable-'
    _false_prefix = 'disable-'


class WithAction(ToggleAction):
    _true_prefix = 'with-'
    _false_prefix = 'without-'


class ArgumentParser(_ArgumentParser):
    def __init__(self, *args, **kwargs):
        _ArgumentParser.__init__(self, *args, **kwargs)
        self.register('action', 'enable', EnableAction)
        self.register('action', 'with', WithAction)

    def _get_option_tuples(self, option_string):
        # Don't try to check prefixes for long options; this is similar to
        # Python 3.5's `allow_abbrev=False`, except this doesn't break combined
        # short options. See <https://bugs.python.org/issue26967>.
        if option_string[:2] == self.prefix_chars * 2:
            return []

        return _ArgumentParser._get_option_tuples(self, option_string)


class BaseFile(object):
    def __init__(self, check_type, kind, must_exist=False):
        self._check_type = check_type
        self._kind = kind
        self.must_exist = must_exist

    def __call__(self, string):
        p = _path.abspath(string)
        if _path.exists(p):
            if not self._check_type(p):
                raise ArgumentTypeError("'{}' is not a {}"
                                        .format(string, self._kind))
        elif self.must_exist:
            raise ArgumentTypeError("'{}' does not exist".format(string))

        return p


class Directory(BaseFile):
    def __init__(self, *args, **kwargs):
        BaseFile.__init__(self, _path.isdir, 'directory', *args, **kwargs)


class File(BaseFile):
    def __init__(self, *args, **kwargs):
        BaseFile.__init__(self, _path.isfile, 'file', *args, **kwargs)


# It'd be nice to just have a UserArgumentParser class with this method but it
# wouldn't propagate to argument groups, so it's easier to just do it this way.
def add_user_argument(parser, *names, **kwargs):
    if any(not i.startswith('--') for i in names):
        raise ValueError('option string must begin with "--"')
    if any(i.startswith('x-') for i in names):
        raise ValueError('"x-" prefix is reserved')

    if parser.usage == 'parse':
        names += tuple('--x-' + i[2:] for i in names)
    return parser.add_argument(*names, **kwargs)
