import os

from builtins import builtin
from languages import ext2lang
import node

class SourceFile(node.Node):
    def __init__(self, name, lang=None):
        node.Node.__init__(self, name)
        self.lang = lang

class HeaderFile(node.Node):
    install_kind = 'data'
    install_dir = 'include'

class ObjectFile(node.Node):
    def __init__(self, name, lang=None):
        node.Node.__init__(self, name)
        self.lang = lang
        self.in_shared_library = False

class Executable(node.Node):
    install_kind = 'program'
    install_dir = 'bin'

class Library(node.Node):
    install_kind = 'program'
    install_dir = 'lib'

class SharedLibrary(Library):
    pass

class StaticLibrary(Library):
    pass

class HeaderDirectory(object):
    install_dir = 'include'

    def __init__(self, path):
        self.path = path

#####

class Compile(node.Edge):
    def __init__(self, target, file, include=None, options=None, deps=None):
        self.file = file
        self.include = include
        self.options = options
        node.Edge.__init__(self, target, deps)

class Link(node.Edge):
    def __init__(self, target, files, libs=None, compile_options=None,
                 link_options=None, deps=None):
        self.files = files
        self.libs = libs
        self.compile_options = compile_options
        self.link_options = link_options
        node.Edge.__init__(self, target, deps)

class Alias(node.Edge):
    pass

class Command(node.Edge):
    def __init__(self, target, cmd, deps=None):
        self.cmd = cmd
        node.Edge.__init__(self, target, deps)

#####

@builtin
def header(build_inputs, name):
    return HeaderFile(name)

@builtin
def object_file(build_inputs, name=None, file=None, include=None, options=None,
                lang=None, deps=None):
    if file is None:
        raise TypeError('"file" argument must not be None')
    if lang is None:
        lang = ext2lang.get( os.path.splitext(file)[1] )
    source_file = node.nodeify(file, SourceFile, lang=lang)

    if name is None:
            name = os.path.splitext(file)[0]
    target = ObjectFile(name, lang)
    build_inputs.add_edge(Compile(target, source_file, include, options, deps))
    return target

@builtin
def object_files(build_inputs, files, include=None, options=None, lang=None):
    return [object_file(build_inputs, file=f, include=include, options=options,
                        lang=lang) for f in files]

def _binary(build_inputs, target, files, libs=None, lang=None,
            include=None, compile_options=None, link_options=None, deps=None):
    def make_obj(x):
        return object_file(build_inputs, file=x, include=include,
                           options=compile_options, lang=lang)

    build_inputs.fallback_default = target
    objects = [node.nodeify(i, ObjectFile, make_obj) for i in files]
    libs = [node.nodeify(i, Library, external=True) for i in libs or []]
    link = Link(target, objects, libs, compile_options, link_options, deps)
    build_inputs.add_edge(link)
    return link

@builtin
def executable(build_inputs, name, *args, **kwargs):
    target = Executable(name)
    _binary(build_inputs, target, *args, **kwargs)
    return target

@builtin
def shared_library(build_inputs, name, *args, **kwargs):
    target = SharedLibrary(name)
    rule = _binary(build_inputs, target, *args, **kwargs)
    for f in rule.files:
        f.in_shared_library = True
    return target

@builtin
def static_library(build_inputs, name, *args, **kwargs):
    target = StaticLibrary(name)
    _binary(build_inputs, target, *args, **kwargs)
    return target

@builtin
def alias(build_inputs, name, deps):
    target = node.Node(name)
    build_inputs.add_edge(Alias(target, deps))
    return target

@builtin
def command(build_inputs, name, cmd, deps=None):
    target = node.Node(name)
    build_inputs.add_edge(Command(target, cmd, deps))
    return target

#####

@builtin
def default(build_inputs, *args):
    build_inputs.default_targets.extend(args)

@builtin
def install(build_inputs, *args):
    for i in args:
        if isinstance(i, HeaderDirectory):
            build_inputs.install_targets.directories.append(i)
        else:
            default(build_inputs, i)
            build_inputs.install_targets.files.append(i)

@builtin
def header_directory(build_inputs, directory):
    return HeaderDirectory(directory)
