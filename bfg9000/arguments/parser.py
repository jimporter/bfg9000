import re as _re
from argparse import *

from .. import path as _path

_ArgumentParser = ArgumentParser
_Action = Action


# Add some simple wrappers to make it easier to specify shell-completion
# behaviors.

def _add_complete(argument, complete):
    if complete is not None:
        argument.complete = complete
    elif isinstance(argument.type, File):
        argument.complete = 'file'
    elif isinstance(argument.type, Directory):
        argument.complete = 'directory'
    return argument


class Action(_Action):
    def __init__(self, *args, complete=None, **kwargs):
        super().__init__(*args, **kwargs)
        _add_complete(self, complete)


class ToggleAction(Action):
    def __init__(self, option_strings, dest, default=False, required=False,
                 complete=None, help=None):
        if len(option_strings) == 0:
            raise ValueError('option string must begin with "--"')

        self.true_strings = [self._prefix(i, self._true_prefix)
                             for i in option_strings]
        self.false_strings = [self._prefix(i, self._false_prefix)
                              for i in option_strings]

        option_strings = self.true_strings + self.false_strings
        super().__init__(option_strings, dest=dest, nargs=0, default=default,
                         required=required, complete=complete, help=help)

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


class BaseFile:
    def __init__(self, must_exist=False):
        self.must_exist = must_exist

    def __call__(self, string):
        p = self._abspath(string)
        if _path.exists(p):
            if not self._check_type(p):
                raise ArgumentTypeError("'{}' is not a {}"
                                        .format(string, self._kind))
        elif self.must_exist:
            raise ArgumentTypeError("'{}' does not exist".format(string))

        return p


class Directory(BaseFile):
    _kind = 'directory'

    @staticmethod
    def _abspath(p):
        return _path.abspath(p, directory=True, absdrive=False)

    @staticmethod
    def _check_type(p):
        return _path.isdir(p)


class File(BaseFile):
    _kind = 'file'

    @staticmethod
    def _abspath(p):
        return _path.abspath(p, directory=False, absdrive=False)

    @staticmethod
    def _check_type(p):
        return _path.isfile(p)


class ArgumentParser(_ArgumentParser):
    @staticmethod
    def _wrap_complete(action):
        def wrapper(*args, complete=None, **kwargs):
            return _add_complete(action(*args, **kwargs), complete)

        return wrapper

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for k, v in self._registries['action'].items():
            self._registries['action'][k] = self._wrap_complete(v)
        self.register('action', 'enable', EnableAction)
        self.register('action', 'with', WithAction)

    def _get_option_tuples(self, option_string):
        # Don't try to check prefixes for long options; this is similar to
        # Python 3.5's `allow_abbrev=False`, except this doesn't break combined
        # short options. See <https://bugs.python.org/issue26967>.
        if option_string[:2] == self.prefix_chars * 2:
            return []

        return super()._get_option_tuples(option_string)


# It'd be nice to just have a UserArgumentParser class with this method but it
# wouldn't propagate to argument groups, so it's easier to just do it this way.
def add_user_argument(parser, *names, **kwargs):
    if any(not i.startswith('--') for i in names):
        raise ValueError('option string must begin with "--"')
    if any(i.startswith('--x-') for i in names):
        raise ValueError('"x-" prefix is reserved')

    if parser.usage == 'parse':
        names += tuple('--x-' + i[2:] for i in names)
    return parser.add_argument(*names, **kwargs)
