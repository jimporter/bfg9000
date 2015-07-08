import os.path

from . import builtin
from .packages import system_executable
from ..build_inputs import Directory, Edge, File, Phony, sourcify
from ..file_types import *
from ..path import Path
from ..utils import flatten, iterate, listify, objectify, shell_listify

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
            raise ValueError('{!r} not found'.format(key))
        else:
            return list.__getitem__(self, key)

#####

class Compile(Edge):
    def __init__(self, build, env, name, file, include=None,
                 packages=None, options=None, lang=None, extra_deps=None):
        if name is None:
            name = os.path.splitext(file)[0]
        include = [sourcify(i, HeaderDirectory) for i in iterate(include)]

        self.file = sourcify(file, SourceFile, lang=lang)
        self.builder = env.compiler(self.file.lang)
        self.include = sum((i.includes for i in iterate(packages)), include)
        self.options = shell_listify(options)
        self.in_shared_library = False

        target = self.builder.output_file(name, self.file.lang)
        Edge.__init__(self, build, target, extra_deps)

class Link(Edge):
    # This is just for MSBuild. XXX: Remove this?
    _project_prefixes = {
        'executable': '',
        'static_library': 'lib',
        'shared_library': 'lib',
    }

    def __init__(self, build, env, mode, name, files, libs=None, include=None,
                 packages=None, compile_options=None, link_options=None,
                 lang=None, extra_deps=None):
        # XXX: Try to detect if a string refers to a shared lib?
        libs = [sourcify(i, Library, StaticLibrary) for i in iterate(libs)]

        self.project_name = self._project_prefixes[mode] + name
        self.files = object_files.bind(build, env)(
            files, include, packages, compile_options, lang
        )
        self.builder = env.linker((i.lang for i in self.files), mode)
        self.libs = sum((i.libraries for i in iterate(packages)), libs)
        self.options = shell_listify(link_options)

        target = self.builder.output_file(name)
        build.fallback_default = target
        Edge.__init__(self, build, target, extra_deps)

class Alias(Edge):
    def __init__(self, build, name, deps=None):
        Edge.__init__(self, build, Phony(name), deps)

class Command(Edge):
    def __init__(self, build, name, cmd=None, cmds=None, extra_deps=None):
        if (cmd is None) == (cmds is None):
            raise ValueError('exactly one of "cmd" or "cmds" must be specified')
        elif cmds is None:
            cmds = [cmd]

        self.cmds = cmds
        Edge.__init__(self, build, Phony(name), extra_deps)

#####

@builtin
def source_file(build, env, name, lang=None):
    # XXX: Add a way to make a generic File object instead of a SourceFile?
    return SourceFile(name, source=Path.srcdir, lang=lang)

@builtin
def header(build, env, name):
    return HeaderFile(name, source=Path.srcdir)

@builtin
def header_directory(build, env, directory):
    return HeaderDirectory(directory, source=Path.srcdir)

@builtin
def object_file(build, env, name=None, file=None, *args, **kwargs):
    if file is None:
        if name is None:
            raise TypeError('expected name')
        return ObjectFile(name, source=Path.srcdir, *args, **kwargs)
    else:
        return Compile(build, env, name, file, *args, **kwargs).target

@builtin
def object_files(build, env, files, *args, **kwargs):
    def _compile(file, *args, **kwargs):
        return Compile(build, env, None, file, *args, **kwargs).target
    return ObjectFiles(objectify(i, ObjectFile, _compile, *args, **kwargs)
                       for i in iterate(files))

@builtin
def executable(build, env, name, files=None, *args, **kwargs):
    if files is None:
        return Executable(name, source=Path.srcdir, *args, **kwargs)
    else:
        return Link(build, env, 'executable', name, files, *args,
                    **kwargs).target

@builtin
def static_library(build, env, name, files=None, *args, **kwargs):
    if files is None:
        return StaticLibrary(name, source=Path.srcdir, *args, **kwargs)
    else:
        return Link(build, env, 'static_library', name, files, *args,
                    **kwargs).target

@builtin
def shared_library(build, env, name, files=None, *args, **kwargs):
    if files is None:
        # XXX: What to do here for Windows, which has a separate DLL file?
        return SharedLibrary(name, source=Path.srcdir, *args, **kwargs)
    else:
        rule = Link(build, env, 'shared_library', name, files, *args, **kwargs)
        for i in rule.files:
            i.creator.in_shared_library = True
        return rule.target

@builtin
def alias(build, env, *args, **kwargs):
    return Alias(build, *args, **kwargs).target

@builtin
def command(build, env, *args, **kwargs):
    return Command(build, *args, **kwargs).target

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
        if isinstance(i, Directory):
            build.install_targets.directories.append(i)
        else:
            default.bind(build, env)(i)
            build.install_targets.files.append(i)

@builtin
def test(build, env, test, options=None, environment=None, driver=None):
    test = sourcify(test, File)
    build.tests.targets.append(test)
    case = TestCase(test, shell_listify(options), environment or {})
    (driver or build.tests).tests.append(case)
    return case

@builtin
def test_driver(build, env, driver, options=None, environment=None,
                parent=None):
    driver = objectify(driver, Executable, system_executable.bind(build, env))
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
