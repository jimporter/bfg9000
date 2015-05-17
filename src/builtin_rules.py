import os

from builtins import builtin
from languages import ext2lang
from utils import iterate, listify, flatten, shell_listify, objectify
import build_inputs


class SourceFile(build_inputs.File):
    def __init__(self, name, lang=None):
        build_inputs.File.__init__(self, name)
        self.lang = lang

class HeaderFile(build_inputs.File):
    install_kind = 'data'
    install_dir = 'include'

class HeaderDirectory(build_inputs.Directory):
    install_dir = 'include'

class ObjectFile(build_inputs.File):
    def __init__(self, name, path, lang=None):
        build_inputs.File.__init__(self, name, path)
        self.lang = lang

class Binary(build_inputs.File):
    install_kind = 'program'

class Executable(Binary):
    install_dir = 'bin'

class Library(Binary):
    install_dir = 'lib'

    def __init__(self, name, lib_name, path):
        Binary.__init__(self, name, path)
        self.lib_name = lib_name

class StaticLibrary(Library):
    pass

class SharedLibrary(Library):
    pass

# Used for Windows DLL files, which aren't linked to directly.
class DynamicLibrary(Library):
    pass

class ExternalLibrary(Library):
    def __init__(self, name):
        # TODO: Handle import libraries specifically?
        Library.__init__(self, name, name, name)

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
def header_directory(build, env, directory):
    return HeaderDirectory(directory)

@builtin
def object_file(build, env, name=None, file=None, include=None, options=None,
                lang=None, deps=None):
    if file is None:
        raise TypeError('"file" argument must not be None')
    if lang is None:
        lang = ext2lang.get( os.path.splitext(file)[1] )
    source_file = objectify(file, SourceFile, lang=lang)
    includes = [objectify(i, HeaderDirectory) for i in iterate(include)]

    if name is None:
        name = os.path.splitext(file)[0]

    builder = env.compiler(source_file.lang)
    head, tail = os.path.split(name)
    path = os.path.join(head, builder.output_name(tail))
    target = ObjectFile(name, path, lang)

    build.add_edge(Compile( target, builder, source_file, includes,
                            shell_listify(options), deps ))
    return target

@builtin
def object_files(build, env, files, include=None, options=None, lang=None):
    def make_object(f):
        return object_file(build, env, file=f, include=include,
                           options=options, lang=lang)
    return [objectify(i, ObjectFile, make_object) for i in iterate(files)]

def _link(build, target, builder, objects, libs=None, options=None, deps=None):
    gen = ( objectify(i, Library, ExternalLibrary)
            for i in flatten(iterate(libs)) )
    libs = [i for i in gen if not isinstance(i, DynamicLibrary)]

    build.add_edge(Link( target, builder, objects, libs,
                         shell_listify(options), deps ))
    build.fallback_default = target
    return target

@builtin
def executable(build, env, name, files, libs=None, include=None,
               compile_options=None, link_options=None, lang=None, deps=None):
    objects = object_files(build, env, files, include, compile_options, lang)
    builder = env.linker((i.lang for i in objects), 'executable')

    head, tail = os.path.split(name)
    path = os.path.join(head, builder.output_name(tail))
    target = Executable(name, path)

    _link(build, target, builder, objects, libs, link_options, deps)
    return target

@builtin
def static_library(build, env, name, files, libs=None, include=None,
                   compile_options=None, link_options=None, lang=None,
                   deps=None):
    objects = object_files(build, env, files, include, compile_options, lang)
    builder = env.linker((i.lang for i in objects), 'static_library')

    head, tail = os.path.split(name)
    path = os.path.join(head, builder.output_name(tail))
    target = StaticLibrary(name, tail, path)

    _link(build, target, builder, objects, libs, link_options, deps)
    return target

@builtin
def shared_library(build, env, name, files, libs=None, include=None,
                   compile_options=None, link_options=None, lang=None,
                   deps=None):
    objects = object_files(build, env, files, include, compile_options, lang)
    for i in objects:
        i.creator.in_shared_library = True
    builder = env.linker((i.lang for i in objects), 'shared_library')

    head, tail = os.path.split(name)
    output = builder.output_name(tail)
    if type(output) == tuple:
        target = ( SharedLibrary(name, tail, os.path.join(head, output[0])),
                   DynamicLibrary(name, tail, os.path.join(head, output[1])) )
    else:
        target = SharedLibrary(name, tail, os.path.join(head, output))

    _link(build, target, builder, objects, libs, link_options, deps)
    return target

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
    build.default_targets.extend(
        i for i in flatten(args) if not i.is_source
    )

@builtin
def install(build, env, *args):
    for i in flatten(args):
        if isinstance(i, build_inputs.Directory):
            build.install_targets.directories.append(i)
        else:
            default(build, i)
            build.install_targets.files.append(i)

@builtin
def global_options(build, env, options, lang):
    if not lang in build.global_options:
        build.global_options[lang] = []
    build.global_options[lang].extend(shell_listify(options))
