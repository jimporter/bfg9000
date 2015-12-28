import os.path
from itertools import chain

from . import builtin
from .packages import system_executable
from ..build_inputs import Directory, Edge, File, Phony, objectify, sourcify
from ..file_types import *
from ..iterutils import iterate, listify, uniques
from ..path import Path, Root
from ..shell import posix as pshell
from .. import version as _version

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
            key = Path(key, Root.srcdir)
        elif isinstance(key, File):
            key = key.path

        if isinstance(key, Path):
            for i in self:
                if i.creator and i.creator.file.path == key:
                    return i
            raise ValueError("{!r} not found".format(key))
        else:
            return list.__getitem__(self, key)

#####

class Compile(Edge):
    def __init__(self, build, env, name, file, include=None,
                 packages=None, options=None, lang=None, extra_deps=None):
        if name is None:
            name = os.path.splitext(file)[0]

        self.file = sourcify(file, SourceFile, lang=lang)
        self.builder = env.compiler(self.file.lang)
        self.includes = [sourcify(i, HeaderDirectory) for i in iterate(include)]
        self.packages = listify(packages)
        self.user_options = pshell.listify(options)
        self.link_options = []

        pkg_includes = chain.from_iterable(i.includes for i in self.packages)
        self.all_includes = uniques(chain(pkg_includes, self.includes))
        self._internal_options = sum(
            (self.builder.include_dir(i) for i in self.all_includes), []
        )

        target = self.builder.output_file(name, self.file.lang)
        Edge.__init__(self, build, target, extra_deps)

    @property
    def options(self):
        return self._internal_options + self.link_options + self.user_options

class Link(Edge):
    __prefixes = {
        'executable': '',
        'static_library': 'lib',
        'shared_library': 'lib',
    }

    @classmethod
    def __name(cls, name, mode):
        head, tail = os.path.split(name)
        return os.path.join(head, cls.__prefixes[mode] + tail)

    def __init__(self, builtins, build, env, mode, name, files, include=None,
                 libs=None, packages=None, compile_options=None,
                 link_options=None, lang=None, extra_deps=None):
        self.name = self.__name(name, mode)
        self.packages = listify(packages)
        self.files = builtins['object_files'](
            files, include, packages, compile_options, lang
        )
        if (len(self.files) == 0 and
            not any(isinstance(i, WholeArchive) for i in libs)):
            raise ValueError('need at least one source file')

        langs = chain([lang], (i.lang for i in self.files))
        self.builder = builder = env.linker(langs, mode)

        # XXX: Try to detect if a string refers to a shared lib?
        self.libs = [sourcify(i, Library, StaticLibrary) for i in iterate(libs)]
        self.all_libs = sum((i.libraries for i in self.packages), self.libs)

        self.user_options = pshell.listify(link_options)
        self._internal_options = []

        target = self.builder.output_file(name)

        if mode == 'static_library':
            if self.options:
                raise ValueError('link options are not allowed for static ' +
                                 'libraries')
            if self.all_libs:
                raise ValueError('libraries cannot be linked into static ' +
                                 'libraries')
        else:
            lib_dirs = sum((i.lib_dirs for i in self.packages), self.all_libs)
            self._internal_options.extend(builder.lib_dirs(lib_dirs, target))
            self._internal_options.extend(builder.import_lib(target))

            links = sum((builder.link_lib(i) for i in self.all_libs), [])
            self.lib_options = links

        for c in (i.creator for i in self.files if i.creator):
            c.link_options.extend(c.builder.link_args(self.name, mode))

        if getattr(self.builder, 'post_install', None):
            target.post_install = self.builder.post_install

        build.fallback_default = target
        Edge.__init__(self, build, target, extra_deps)

    @property
    def options(self):
        return self._internal_options + self.user_options

class Alias(Edge):
    def __init__(self, build, name, deps=None):
        Edge.__init__(self, build, Phony(name), deps)

class Command(Edge):
    def __init__(self, build, name, cmd=None, cmds=None, environment=None,
                 extra_deps=None):
        if (cmd is None) == (cmds is None):
            raise ValueError('exactly one of "cmd" or "cmds" must be specified')
        elif cmds is None:
            cmds = [cmd]

        self.cmds = cmds
        self.env = environment or {}
        Edge.__init__(self, build, Phony(name), extra_deps)

#####

@builtin
def source_file(name, lang=None):
    # XXX: Add a way to make a generic File object instead of a SourceFile?
    return SourceFile(name, root=Root.srcdir, lang=lang)

@builtin
def header(name):
    return HeaderFile(name, root=Root.srcdir)

@builtin
def header_directory(directory, system=False):
    return HeaderDirectory(directory, Root.srcdir, system)

@builtin
def whole_archive(lib):
    lib = sourcify(lib, Library, StaticLibrary)
    return WholeArchive(lib)

@builtin.globals('build_inputs', 'env')
def object_file(build, env, name=None, file=None, *args, **kwargs):
    if file is None:
        if name is None:
            raise TypeError('expected name')
        return ObjectFile(name, root=Root.srcdir, *args, **kwargs)
    else:
        return Compile(build, env, name, file, *args, **kwargs).target

@builtin.globals('build_inputs', 'env')
def object_files(build, env, files, *args, **kwargs):
    def _compile(file, *args, **kwargs):
        return Compile(build, env, None, file, *args, **kwargs).target
    return ObjectFiles(objectify(i, ObjectFile, _compile, *args, **kwargs)
                       for i in iterate(files))

@builtin.globals('builtins', 'build_inputs', 'env')
def executable(builtins, build, env, name, files=None, *args, **kwargs):
    if files is None:
        return Executable(name, root=Root.srcdir, *args, **kwargs)
    else:
        return Link(builtins, build, env, 'executable', name, files, *args,
                    **kwargs).target

@builtin.globals('builtins', 'build_inputs', 'env')
def static_library(builtins, build, env, name, files=None, *args, **kwargs):
    if files is None:
        return StaticLibrary(name, root=Root.srcdir, *args, **kwargs)
    else:
        return Link(builtins, build, env, 'static_library', name, files, *args,
                    **kwargs).target

@builtin.globals('builtins', 'build_inputs', 'env')
def shared_library(builtins, build, env, name, files=None, *args, **kwargs):
    if files is None:
        # XXX: What to do here for Windows, which has a separate DLL file?
        return SharedLibrary(name, root=Root.srcdir, *args, **kwargs)
    else:
        return Link(builtins, build, env, 'shared_library', name, files, *args,
                    **kwargs).target

@builtin.globals('build_inputs')
def alias(build, *args, **kwargs):
    return Alias(build, *args, **kwargs).target

@builtin.globals('build_inputs')
def command(build, *args, **kwargs):
    return Command(build, *args, **kwargs).target

#####

@builtin.globals('build_inputs')
def default(build, *args):
    if len(args) == 0:
        raise ValueError('expected at least one argument')
    build.default_targets.extend(i for i in args if i.creator)

@builtin.globals('builtins', 'build_inputs')
def install(builtins, build, *args, **kwargs):
    def _flatten(args):
        for i in args:
            for j in i.all:
                yield j

    if len(args) == 0:
        raise ValueError('expected at least one argument')
    all_files = kwargs.pop('all', True)

    for i in _flatten(args) if all_files else args:
        if isinstance(i, Directory):
            build.install_targets.directories.append(i)
        else:
            builtins['default'](i)
            build.install_targets.files.append(i)

@builtin.globals('build_inputs')
def test(build, test, options=None, environment=None, driver=None):
    if driver and environment:
        raise TypeError('only one of "driver" and "environment" may be ' +
                        'specified')

    test = sourcify(test, File)
    build.tests.targets.append(test)
    case = TestCase(test, pshell.listify(options), environment or {})
    (driver or build.tests).tests.append(case)
    return case

@builtin.globals('builtins', 'build_inputs', 'env')
def test_driver(builtins, build, env, driver, options=None, environment=None,
                parent=None):
    if parent and environment:
        raise TypeError('only one of "parent" and "environment" may be ' +
                        'specified')

    driver = objectify(driver, Executable, builtins['system_executable'])
    result = TestDriver(driver, pshell.listify(options), environment or {})
    (parent or build.tests).tests.append(result)
    return result

@builtin.globals('build_inputs')
def test_deps(build, *args):
    if len(args) == 0:
        raise ValueError('expected at least one argument')
    build.tests.extra_deps.extend(args)

@builtin.globals('build_inputs')
def global_options(build, options, lang):
    if not lang in build.global_options:
        build.global_options[lang] = []
    build.global_options[lang].extend(pshell.listify(options))

@builtin.globals('build_inputs')
def global_link_options(build, options):
    build.global_link_options.extend(pshell.listify(options))
