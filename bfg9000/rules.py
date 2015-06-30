import os.path

from . import build_inputs
from .builtins import builtin
from .file_types import *
from .languages import ext2lang
from .path import Path
from .utils import flatten, iterate, listify, objectify, shell_listify

class TestCase(object):
    def __init__(self, target, options, env):
        self.target = target
        self.options = options
        self.env = env

class TestDriver(object):
    def __init__(self, target, options, env):
        self.target = target
        self.options = options
        self.env = env
        self.tests = []

class ObjectFiles(list):
    def __getitem__(self, key):
        if isinstance(key, basestring):
            for i in self:
                if i.creator and i.creator.file.path.path == key:
                    return i
            raise ValueError('{} not found'.format(repr(key)))
        else:
            return list.__getitem__(self, key)

#####

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
def source_file(build, env, name, lang=None):
    if lang is None:
        lang = ext2lang.get( os.path.splitext(name)[1] )
    return SourceFile(name, source=Path.srcdir, lang=lang)

@builtin
def header(build, env, name):
    return HeaderFile(name, source=Path.srcdir)

@builtin
def header_directory(build, env, directory):
    return HeaderDirectory(directory, source=Path.srcdir)

@builtin
def object_file(build, env, name=None, file=None, include=None, packages=None,
                options=None, lang=None, extra_deps=None):
    if file is None:
        raise TypeError('"file" argument must not be None')
    if lang is None:
        lang = ext2lang.get( os.path.splitext(file)[1] )
    source_file = objectify(file, SourceFile, source=Path.srcdir, lang=lang)
    includes = [objectify(i, HeaderDirectory, source=Path.srcdir)
                for i in iterate(include)]
    includes += sum((i.includes for i in iterate(packages)), [])

    if name is None:
        name = os.path.splitext(file)[0]

    builder = env.compiler(source_file.lang)
    target = builder.output_file(name, lang)
    build.add_edge(Compile( target, builder, source_file, includes,
                            shell_listify(options), extra_deps ))
    return target

@builtin
def object_files(build, env, files, include=None, packages=None, options=None,
                 lang=None):
    def make_object(f):
        return object_file(build, env, file=f, include=include,
                           options=options, lang=lang)
    return ObjectFiles(objectify(i, ObjectFile, make_object)
                       for i in iterate(files))

def _link(build, env, mode, project_name, name, files, libs=None,
          include=None, packages=None, compile_options=None, link_options=None,
          lang=None, extra_deps=None):
    objects = object_files(build, env, files, include, packages,
                           compile_options, lang)
    libs = listify(libs, always_copy=True) # FIXME: Type-check/objectify?
    libs += sum((i.libraries for i in iterate(packages)), [])

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
    if len(args) == 0:
        raise ValueError('expected at least one argument')
    build.default_targets.extend(
        i for i in flatten(args) if i.creator
    )

@builtin
def install(build, env, *args):
    if len(args) == 0:
        raise ValueError('expected at least one argument')
    for i in flatten(args):
        if isinstance(i, build_inputs.Directory):
            build.install_targets.directories.append(i)
        else:
            default(build, env, i)
            build.install_targets.files.append(i)

@builtin
def test(build, env, test, options=None, environment=None, driver=None):
    test = objectify(test, build_inputs.File, source=Path.srcdir)
    build.tests.targets.append(test)
    case = TestCase(test, shell_listify(options), environment or {})
    (driver or build.tests).tests.append(case)
    return case

@builtin
def test_driver(build, env, driver, options=None, environment=None,
                parent=None):
    driver = objectify(driver, Executable, ExternalExecutable)
    result = TestDriver(driver, shell_listify(options), environment or {})
    (parent or build.tests).tests.append(result)
    return result

@builtin
def test_deps(build, env, *args):
    build.tests.extra_deps.extend(
        i for i in flatten(args) if i.creator
    )

@builtin
def global_options(build, env, options, lang):
    if not lang in build.global_options:
        build.global_options[lang] = []
    build.global_options[lang].extend(shell_listify(options))

@builtin
def global_link_options(build, env, options):
    build.global_link_options.extend(shell_listify(options))
