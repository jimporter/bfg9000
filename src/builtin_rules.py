import os

from builtins import builtin
from languages import ext2lang
import build_inputs
import utils

class SourceFile(build_inputs.File):
    def __init__(self, name, lang=None):
        build_inputs.File.__init__(self, name)
        self.lang = lang

class HeaderFile(build_inputs.File):
    install_kind = 'data'
    install_dir = 'include'

class ObjectFile(build_inputs.File):
    def __init__(self, name, path, lang=None):
        build_inputs.File.__init__(self, name, path)
        self.lang = lang

class Binary(build_inputs.File):
    install_kind = 'program'

class Executable(Binary):
    install_dir = 'bin'
    mode = 'executable'

class Library(Binary):
    install_dir = 'lib'

    def __init__(self, name, lib_name, path):
        Binary.__init__(self, name, path)
        self.lib_name = lib_name

class SharedLibrary(Library):
    mode = 'shared_library'

    def __init__(self, name, lib_name, path, dll_path=None):
        Library.__init__(self, name, lib_name, path)
        if dll_path:
            self.dll_path = dll_path

class StaticLibrary(Library):
    mode = 'static_library'

class ExternalLibrary(Library):
    def __init__(self, name):
        # TODO: Handle import libraries specifically?
        Library.__init__(self, name, name, name)

class HeaderDirectory(build_inputs.Directory):
    install_dir = 'include'

#####

class Compile(build_inputs.Edge):
    def __init__(self, target, builder, file, include, options, deps):
        self.builder = builder
        self.file = file
        self.include = include
        self.options = options
        self.in_shared_library = False
        build_inputs.Edge.__init__(self, target, deps)

class Link(build_inputs.Edge):
    def __init__(self, target, builder, files, libs, options, deps):
        self.builder = builder
        self.files = files
        self.libs = libs
        self.options = options
        build_inputs.Edge.__init__(self, target, deps)

class Alias(build_inputs.Edge):
    pass

class Command(build_inputs.Edge):
    def __init__(self, target, cmd, deps):
        self.cmd = cmd
        build_inputs.Edge.__init__(self, target, deps)

#####

@builtin
def header(build, env, name):
    return HeaderFile(name)

@builtin
def object_file(build, env, name=None, file=None, include=None, options=None,
                lang=None, deps=None):
    if file is None:
        raise TypeError('"file" argument must not be None')
    if lang is None:
        lang = ext2lang.get( os.path.splitext(file)[1] )
    source_file = utils.objectify(file, SourceFile, lang=lang)
    includes = utils.objectify_list(include, HeaderDirectory)

    if name is None:
        name = os.path.splitext(file)[0]

    builder = env.compiler(source_file.lang)
    head, tail = os.path.split(name)
    path = os.path.join(head, builder.output_name(tail))
    target = ObjectFile(name, path, lang)

    build.add_edge(Compile( target, builder, source_file, includes,
                            utils.shell_listify(options), deps ))
    return target

@builtin
def object_files(build, env, files, include=None, options=None, lang=None):
    def make_object(f):
        return object_file(build, env, file=f, include=include,
                           options=options, lang=lang)
    return utils.objectify_list(files, ObjectFile, make_object)

def _link(build, target, builder, objects, libs=None, options=None, deps=None):
    libs = utils.objectify_list(libs, Library, ExternalLibrary)
    build.add_edge(Link( target, builder, objects, libs,
                         utils.shell_listify(options), deps ))
    build.fallback_default = target
    return target

@builtin
def executable(build, env, name, files, libs=None, include=None,
               compile_options=None, link_options=None, lang=None, deps=None):
    objects = object_files(build, env, files, include, compile_options, lang)
    builder = env.linker((i.lang for i in objects), Executable.mode)

    head, tail = os.path.split(name)
    path = os.path.join(head, builder.output_name(tail))
    target = Executable(name, path)
    _link(build, target, builder, objects, libs, link_options, deps)
    return target

def _library(build, env, target_type, name, files, libs=None, include=None,
             compile_options=None, link_options=None, lang=None, deps=None):
    objects = object_files(build, env, files, include, compile_options, lang)
    builder = env.linker((i.lang for i in objects), target_type.mode)

    head, tail = os.path.split(name)
    paths = [ os.path.join(head, i) for i in
              utils.listify(builder.output_name(tail)) ]
    target = target_type(name, tail, *paths)
    _link(build, target, builder, objects, libs, link_options, deps)
    return target

@builtin
def shared_library(build, env, *args, **kwargs):
    target = _library(build, env, SharedLibrary, *args, **kwargs)
    for f in target.creator.files:
        f.creator.in_shared_library = True
    return target

@builtin
def static_library(build, env, *args, **kwargs):
    return _library(build, env, StaticLibrary, *args, **kwargs)

@builtin
def alias(build, env, name, deps):
    target = build_inputs.Node(name)
    build.add_edge(Alias(target, deps))
    return target

@builtin
def command(build, env, name, cmd, deps=None):
    target = build_inputs.Node(name)
    build.add_edge(Command(target, cmd, deps))
    return target

#####

@builtin
def default(build, env, *args):
    build.default_targets.extend(i for i in args if not i.is_source)

@builtin
def install(build, env, *args):
    for i in args:
        if isinstance(i, build_inputs.Directory):
            build.install_targets.directories.append(i)
        else:
            default(build, i)
            build.install_targets.files.append(i)

@builtin
def header_directory(build, env, directory):
    return HeaderDirectory(directory)

@builtin
def global_options(build, env, options, lang):
    if not lang in build.global_options:
        build.global_options[lang] = []
    build.global_options[lang].extend(utils.shell_listify(options))
