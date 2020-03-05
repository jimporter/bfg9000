from . import builtin
from ..arguments.parser import add_user_argument


@builtin.getter()
def argv(context):
    return context.argv


@builtin.function(context='options')
def argument(context, *args, **kwargs):
    names = ['--' + i for i in args]
    add_user_argument(context.parser, *names, **kwargs)
