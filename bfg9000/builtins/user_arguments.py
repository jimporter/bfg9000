from . import builtin
from ..arguments.parser import add_user_argument


@builtin.getter('argv')
def argv(_argv):
    return _argv


@builtin.function('parser', context='options')
def argument(parser, *args, **kwargs):
    names = ['--' + i for i in args]
    add_user_argument(parser, *names, **kwargs)
