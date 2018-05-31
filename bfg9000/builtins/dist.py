from collections import OrderedDict

from . import builtin
from ..iterutils import iterate
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..path import Path, Root

_exts = OrderedDict(
    gzip='.tar.gz',
    bzip2='.tar.bz2',
    zip='.zip',
)


@builtin.function('builtins')
def extra_dist(builtins, files=None, dirs=None):
    for i in iterate(files):
        builtins['generic_file'](i)
    for i in iterate(dirs):
        builtins['directory'](i, include='*')


def _dist_command(format, build_inputs, buildfile, env):
    srcdir = Path('.', Root.srcdir)
    doppel = env.tool('doppel')

    project = build_inputs['project']
    dstname = project.name
    if project.version:
        dstname += '-' + str(project.version)

    return doppel(
        'archive', [i.path.relpath(srcdir) for i in build_inputs.sources()],
        Path(dstname + _exts[format]), directory=srcdir, format=format,
        dest_prefix=dstname
    )


@make.post_rule
def make_dist_rule(build_inputs, buildfile, env):
    for fmt in _exts:
        buildfile.rule(
            target='dist-{}'.format(fmt),
            recipe=[_dist_command(fmt, build_inputs, buildfile, env)],
            phony=True
        )

    buildfile.rule(
        target='dist',
        deps='dist-gzip',
        phony=True
    )


@ninja.post_rule
def ninja_dist_rule(build_inputs, buildfile, env):
    for fmt in _exts:
        ninja.command_build(
            buildfile, env,
            output='dist-{}'.format(fmt),
            command=_dist_command(fmt, build_inputs, buildfile, env)
        )

    buildfile.build(
        output='dist',
        rule='phony',
        inputs='dist-gzip'
    )
