from collections import OrderedDict

from .hooks import builtin
from ..iterutils import iterate
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..path import Path, Root

_exts = OrderedDict(
    gzip='.tar.gz',
    bzip2='.tar.bz2',
    zip='.zip',
)


@builtin.globals('builtins')
def extra_dist(builtins, files=None, dirs=None):
    for i in iterate(files):
        builtins['generic_file'](i)
    for i in iterate(dirs):
        builtins['directory'](i)


def _dist_command(backend, format, build_inputs, buildfile, env):
    srcdir = Path('.', Root.srcdir)
    doppel = env.tool('doppel')
    cmd = backend.cmd_var(doppel, buildfile)

    project = build_inputs['project']
    dstname = project.name
    if project.version:
        dstname += '-' + str(project.version)

    return [doppel.archive(
        cmd, format, [i.path.relpath(srcdir) for i in build_inputs.sources()],
        Path(dstname + _exts[format]), directory=srcdir, dest_prefix=dstname
    )]


@make.post_rule
def make_dist_rule(build_inputs, buildfile, env):
    for fmt in _exts:
        buildfile.rule(
            target='dist-{}'.format(fmt),
            recipe=_dist_command(make, fmt, build_inputs, buildfile, env),
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
            commands=_dist_command(ninja, fmt, build_inputs, buildfile, env)
        )

    buildfile.build(
        output='dist',
        rule='phony',
        inputs='dist-gzip'
    )
