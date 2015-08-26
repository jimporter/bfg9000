import os
from itertools import chain

from . import version
from .syntax import *
from ... import iterutils
from ...makedirs import makedirs

priority = 1 if version is not None else 0

def link_mode(mode):
    return {
        'executable'    : 'Application',
        'static_library': 'StaticLibrary',
        'shared_library': 'DynamicLibrary',
    }[mode]

def reduce_options(files, global_options):
    compilers = iterutils.uniques(i.creator.builder for i in files)
    langs = iterutils.uniques(i.lang for i in files)

    per_file_opts = []
    for i in files:
        opts = i.creator.options
        if opts not in per_file_opts:
            per_file_opts.append(opts)

    return list(chain(
        chain.from_iterable(i.global_args for i in compilers),
        chain.from_iterable(global_options.get(i, []) for i in langs),
        chain.from_iterable(per_file_opts)
    ))

def reduce_includes(files):
    return iterutils.uniques(chain.from_iterable(
        (i.creator.include for i in files)
    ))

def write(env, build_inputs):
    uuids = UUIDMap(os.path.join(env.builddir, '.bfg_uuid'))

    projects = []
    project_map = {}
    # TODO: Handle default().
    for e in build_inputs.edges:
        if type(e).__name__ == 'Link':
            # By definition, a dependency for an edge must already be defined by
            # the time the edge is created, so we can map *all* the dependencies
            # to their associated projects by looking at the projects we've
            # already created.
            dependencies = []
            for dep in e.libs:
                if not dep.creator:
                    continue
                if id(dep.creator.target) not in project_map:
                    raise ValueError('unknown dependency for {!r}'.format(dep))
                dependencies.append(project_map[id(dep.creator.target)])

            project = VcxProject(
                name=e.project_name,
                uuid=uuids[e.project_name],
                version=env.getvar('VISUALSTUDIOVERSION'),
                mode=link_mode(e.builder.mode),
                platform=env.getvar('PLATFORM'),
                output_file=e.target,
                srcdir=env.srcdir,
                files=[i.creator.file for i in e.files],
                compile_options=reduce_options(
                    e.files, build_inputs.global_options
                ),
                includes=reduce_includes(e.files),
                link_options=e.builder.global_args +
                    build_inputs.global_link_options + e.options,
                libs=e.libs,
                dependencies=dependencies,
            )
            projects.append(project)
            project_map[id(e.target)] = project

    with open(os.path.join(env.builddir, 'project.sln'), 'w') as out:
        write_solution(out, uuids[''], projects)
    for p in projects:
        projfile = os.path.join(env.builddir, p.path)
        makedirs(os.path.dirname(projfile), exist_ok=True)
        with open(projfile, 'w') as out:
            p.write(out)
    uuids.save()
