import argparse
import re

from .hooks import builtin, optbuiltin

help_description = """
These arguments are defined by the build.opts file in the project's source
directory. To disambiguate them from built-in arguments, you may prefix the
argument name with `-x`. For example, `--foo` may also be written as `--x-foo`.
"""


class ToggleAction(argparse.Action):
    def __init__(self, option_strings, dest, default=False, required=False,
                 help=None):
        self.true_strings = [self._prefix(i, self._true_prefix)
                             for i in option_strings]
        self.false_strings = [self._prefix(i, self._false_prefix)
                              for i in option_strings]

        if default:
            option_strings = self.false_strings + self.true_strings
        else:
            option_strings = self.true_strings + self.false_strings

        argparse.Action.__init__(self, option_strings, dest=dest, nargs=0,
                                 default=default, required=required, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        value = option_string in self.true_strings
        setattr(namespace, self.dest, value)

    @staticmethod
    def _prefix(s, prefix):
        if s.startswith('--'):
            raise ValueError('option string must begin with "--"')
        return re.sub('(^--(x-)?)', r'\1' + prefix, s)


class EnableAction(ToggleAction):
    _true_prefix = 'enable-'
    _false_prefix = 'disable-'


class WithAction(ToggleAction):
    _true_prefix = 'with-'
    _false_prefix = 'without-'


def make_parser(prog, parents=None, usage='parse'):
    parser = argparse.ArgumentParser(prog=prog, parents=parents,
                                     add_help=False)
    parser.register('action', 'enable', EnableAction)
    parser.register('action', 'with', WithAction)

    group = parser.add_argument_group('user arguments',
                                      description=help_description)
    group.usage = usage
    return parser, group


@builtin.getter('argv')
def argv(_argv):
    return _argv


@optbuiltin.globals('parser')
def argument(parser, *args, **kwargs):
    if any(i.startswith('x-') for i in args):
        raise ValueError('"x-" prefix is reserved')

    names = ['--' + i for i in args]
    if parser.usage == 'parse':
        names += ['--x-' + i for i in args]
    parser.add_argument(*names, **kwargs)
