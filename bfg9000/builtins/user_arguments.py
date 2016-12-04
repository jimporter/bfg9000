from .hooks import builtin, optbuiltin
from ..arguments.parser import add_user_argument


@builtin.getter('argv')
def argv(_argv):
    return _argv


@optbuiltin.globals('parser')
def argument(parser, *args, **kwargs):
    names = ['--' + i for i in args]
    add_user_argument(parser, *names, **kwargs)
