import fnmatch
import os

from . import build_inputs
from .builtins import builtin
from .file_types import *
from .languages import ext2lang
from .path import Path
from .utils import flatten, iterate, listify, objectify, shell_listify

class Compile(build_inputs.Edge):
    def __init__(self, target, builder, file, include, options, extra_deps):
        self.builder = builder
        self.file = file
        self.include = include
        self.options = options
        self.in_shared_library = False
        build_inputs.Edge.__init__(self, target, extra_deps)

class Link(build_inputs.Edge):
    def __init__(self, target, project_name, builder, files, libs, options,
                 extra_deps):
        # This is just for MSBuild. XXX: Remove this?
        self.project_name = project_name

        self.builder = builder
        self.files = files
        self.libs = libs
        self.options = options
        build_inputs.Edge.__init__(self, target, extra_deps)

class Alias(build_inputs.Edge):
    pass

class Command(build_inputs.Edge):
    def __init__(self, target, cmds, extra_deps):
        self.cmds = cmds
        build_inputs.Edge.__init__(self, target, extra_deps)

#####

@builtin
def header(build, env, name):
    return HeaderFile(name, source=Path.srcdir)

@builtin
def header_directory(build, env, directory):
    return HeaderDirectory(directory, source=Path.srcdir)

@builtin
def object_file(build, env, name=None, file=None, include=None, options=None,
                lang=None, extra_deps=None):
    if file is None:
        raise TypeError('"file" argument must not be None')
    if lang is None:
        lang = ext2lang.get( os.path.splitext(file)[1] )
    source_file = objectify(file, SourceFile, source=Path.srcdir, lang=lang)
    includes = [objectify(i, HeaderDirectory, source=Path.srcdir)
                for i in iterate(include)]

    if name is None:
        name = os.path.splitext(file)[0]

    builder = env.compiler(source_file.lang)
    target = builder.output_file(name, lang)
    build.add_edge(Compile( target, builder, source_file, includes,
                            shell_listify(options), extra_deps ))
    return target

@builtin
def object_files(build, env, files, include=None, options=None, lang=None):
    def make_object(f):
        return object_file(build, env, file=f, include=include,
                           options=options, lang=lang)
    return [objectify(i, ObjectFile, make_object) for i in iterate(files)]

def _link(build, env, mode, project_name, name, files, libs=None,
          include=None, compile_options=None, link_options=None, lang=None,
          extra_deps=None):
    objects = object_files(build, env, files, include, compile_options, lang)

    # Flatten the list of libraries and remove any DynamicLibraries (since they
    # can't be linked to at build time).
    libs = [ objectify(i, Library, ExternalLibrary) for i in
             flatten(iterate(libs)) if not isinstance(i, DynamicLibrary) ]

    builder = env.linker((i.lang for i in objects), mode)
    target = builder.output_file(name)
    rule = Link(target, project_name, builder, objects, libs,
                shell_listify(link_options), extra_deps)
    build.add_edge(rule)
    build.fallback_default = target
    return target, rule

@builtin
def executable(build, env, name, *args, **kwargs):
    return _link(build, env, 'executable', name, name, *args, **kwargs)[0]

@builtin
def static_library(build, env, name, *args, **kwargs):
    return _link(build, env, 'static_library', 'lib' + name, name, *args,
                 **kwargs)[0]

@builtin
def shared_library(build, env, name, *args, **kwargs):
    target, rule = _link(build, env, 'shared_library', 'lib' + name, name,
                         *args, **kwargs)
    for i in rule.files:
        i.creator.in_shared_library = True
    return target

@builtin
def alias(build, env, name, deps):
    target = build_inputs.Phony(name)
    build.add_edge(Alias(target, deps))
    return target

@builtin
def command(build, env, name, cmd=None, cmds=None, extra_deps=None):
    if (cmd is None) == (cmds is None):
        raise ValueError('exactly one of "cmd" or "cmds" must be specified')
    elif cmds is None:
        cmds = [cmd]

    target = build_inputs.Phony(name)
    build.add_edge(Command(target, cmds, extra_deps))
    return target

#####

@builtin
def default(build, env, *args):
    build.default_targets.extend(
        i for i in flatten(args) if i.creator
    )

@builtin
def install(build, env, *args):
    for i in flatten(args):
        if isinstance(i, build_inputs.Directory):
            build.install_targets.directories.append(i)
        else:
            default(build, i)
            build.install_targets.files.append(i)

class TestDriver(object):
    def __init__(self, driver):
        self.driver = driver
        self.test_targets = []

@builtin
def test(build, env, test, driver=None):
    build.all_tests.append(test)
    (driver or build).test_targets.append(test)

@builtin
def test_driver(build, env, driver, parent=None):
    result = TestDriver(driver)
    (parent or build).test_targets.append(result)
    return result

@builtin
def global_options(build, env, options, lang):
    if not lang in build.global_options:
        build.global_options[lang] = []
    build.global_options[lang].extend(shell_listify(options))

@builtin
def find(build_inputs, env, base='.', name='*', type=None):
    results = []
    for path, dirs, files in os.walk(base):
        if type != 'f':
            results.extend((
                os.path.join(path, i) for i in fnmatch.filter(dirs, name)
            ))
        if type != 'd':
            results.extend((
                os.path.join(path, i) for i in fnmatch.filter(files, name)
            ))
    return results
