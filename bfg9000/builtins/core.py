import warnings

from . import builtin
from .. import build, exceptions, log, safe_str


@builtin.getter(name='env', context=('build', 'options'))
def getenv(context):
    return context.env


@builtin.default(context='*')
def warning(*args):
    warnings.warn(log.format_message(*args))


@builtin.default(context='*')
def info(*args, show_stack=False):
    log.log_message(log.INFO, *args, show_stack=show_stack, stacklevel=1)


@builtin.default(context='*')
def debug(*args, show_stack=True):
    log.log_message(log.DEBUG, *args, show_stack=show_stack, stacklevel=1)


for i in dir(exceptions):
    i = getattr(exceptions, i)
    if isinstance(i, type):
        builtin.default(context='*')(i)

for i in (safe_str.safe_str, safe_str.safe_format):
    builtin.default(context='*')(i)


@builtin.function(context=('build', 'options'))
def submodule(context, path):
    path = context['relpath'](path).append(context.filename)
    return build.execute_file(context, path).exports


@builtin.function(context=('build', 'options'))
def export(context, **kwargs):
    context.exports.update(kwargs)
