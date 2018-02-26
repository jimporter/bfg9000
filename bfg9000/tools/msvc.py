import os.path
import re
from itertools import chain

from . import pkg_config
from .common import BuildCommand, check_which
from .. import shell
from ..arguments.windows import ArgumentParser
from ..builtins.file_types import generated_file
from ..exceptions import PackageResolutionError
from ..file_types import *
from ..iterutils import default_sentinel, iterate, listify, uniques
from ..languages import lang2src
from ..path import Path, Root
from ..versioning import detect_version


class MsvcBuilder(object):
    def __init__(self, env, lang, name, command, cflags_name, cflags,
                 version_output):
        self.lang = lang
        self.object_format = env.platform.object_format

        if 'Microsoft (R)' in version_output:
            self.brand = 'msvc'
            self.version = detect_version(version_output)
        else:
            # XXX: Detect clang-cl.
            self.brand = 'unknown'
            self.version = None

        # Look for the last argument that looks like our compiler and use its
        # directory as the base directory to find the linkers.
        origin = ''
        for i in reversed(command):
            if os.path.basename(i) in ('cl', 'cl.exe'):
                origin = os.path.dirname(i)
        link_command = check_which(
            env.getvar('VCLINK', os.path.join(origin, 'link')),
            env.variables, kind='dynamic linker'.format(lang)
        )
        lib_command = check_which(
            env.getvar('VCLIB', os.path.join(origin, 'lib')),
            env.variables, kind='static linker'.format(lang)
        )

        ldflags = shell.split(env.getvar('LDFLAGS', ''))
        ldlibs = shell.split(env.getvar('LDLIBS', ''))

        self.compiler = MsvcCompiler(self, env, name, command, cflags_name,
                                     cflags)
        self.pch_compiler = MsvcPchCompiler(self, env, name, command,
                                            cflags_name, cflags)
        self._linkers = {
            'executable': MsvcExecutableLinker(
                self, env, link_command, ldflags, ldlibs
            ),
            'shared_library': MsvcSharedLibraryLinker(
                self, env, link_command, ldflags, ldlibs
            ),
            'static_library': MsvcStaticLinker(
                self, env, lib_command
            ),
        }
        self.packages = MsvcPackageResolver(self, env)
        self.runner = None

    @staticmethod
    def check_command(env, command):
        return env.execute(command + ['/?'], stdout=shell.Mode.pipe,
                           stderr=shell.Mode.stdout)

    @property
    def flavor(self):
        return 'msvc'

    @property
    def family(self):
        return 'native'

    @property
    def auto_link(self):
        return True

    @property
    def can_dual_link(self):
        return False

    def linker(self, mode):
        return self._linkers[mode]


class MsvcBaseCompiler(BuildCommand):
    def __init__(self, builder, env, rule_name, command_var, command,
                 cflags_name, cflags):
        BuildCommand.__init__(self, builder, env, rule_name, command_var,
                              command, flags=(cflags_name, cflags))

    @property
    def brand(self):
        return self.builder.brand

    @property
    def version(self):
        return self.builder.version

    @property
    def flavor(self):
        return 'msvc'

    @property
    def deps_flavor(self):
        return 'msvc'

    @property
    def num_outputs(self):
        return 1

    @property
    def depends_on_libs(self):
        return False

    def search_dirs(self, strict=False):
        cpath = [os.path.abspath(i) for i in
                 self.env.getvar('CPATH', '').split(os.pathsep)]
        include = [os.path.abspath(i) for i in
                   self.env.getvar('INCLUDE', '').split(os.pathsep)]
        return cpath + include

    def _call(self, cmd, input, output, deps=None, flags=None):
        result = list(chain( cmd, self._always_flags, iterate(flags) ))
        if deps:
            result.append('/showIncludes')
        result.extend(['/c', input])
        result.append('/Fo' + output)
        return result

    @property
    def _always_flags(self):
        return ['/nologo']

    def _include_dir(self, directory, syntax):
        prefix = '-I' if syntax == 'cc' else '/I'
        return [prefix + directory.path]

    def _include_pch(self, pch):
        return ['/Yu' + pch.header_name]

    def flags(self, options, output, pkg=False):
        syntax = getattr(options, 'syntax', 'msvc')
        includes = getattr(options, 'includes', [])
        pch = getattr(options, 'pch', None)
        return sum((self._include_dir(i, syntax) for i in includes),
                   self._include_pch(pch) if pch else [])

    def link_flags(self, mode, defines):
        return ['/D' + i for i in defines]

    def parse_flags(self, flags):
        parser = ArgumentParser()
        parser.add('/nologo')
        parser.add('/D', '-D', type=list, dest='defines')
        parser.add('/I', '-I', type=list, dest='includes')

        warn = parser.add('/W', type=dict, dest='warnings')
        warn.add('0', '1', '2', '3', '4', 'all', dest='level')
        warn.add('X', type=bool, dest='as_error')
        warn.add('X-', type=bool, dest='as_error', value=False)

        pch = parser.add('/Y', type=dict, dest='pch')
        pch.add('u', type=str, dest='use')
        pch.add('c', type=str, dest='create')

        result, extra = parser.parse_known(flags)
        result['extra'] = extra
        return result


class MsvcCompiler(MsvcBaseCompiler):
    def __init__(self, builder, env, name, command, cflags_name, cflags):
        MsvcBaseCompiler.__init__(self, builder, env, name, name, command,
                                  cflags_name, cflags)

    @property
    def accepts_pch(self):
        return True

    def output_file(self, name, options):
        output = ObjectFile(Path(name + '.obj'),
                            self.builder.object_format, self.lang)
        if options.pch:
            output.extra_objects = [options.pch.object_file]
        return output


class MsvcPchCompiler(MsvcBaseCompiler):
    def __init__(self, builder, env, name, command, cflags_name, cflags):
        MsvcBaseCompiler.__init__(self, builder, env, name + '_pch', name,
                                  command, cflags_name, cflags)

    @property
    def num_outputs(self):
        return 2

    @property
    def accepts_pch(self):
        # You can't to pass a PCH to a PCH compiler!
        return False

    def _call(self, cmd, input, output, deps=None, flags=None):
        output = listify(output)
        result = MsvcBaseCompiler._call(self, cmd, input, output[1], deps,
                                        flags)
        result.append('/Fp' + output[0])
        return result

    def pre_build(self, build, options, name):
        if options.pch_source is None:
            header = getattr(options, 'file', None)
            ext = lang2src[header.lang][0]
            options.pch_source = SourceFile(header.path.stripext(ext).reroot(),
                                            header.lang)
            options.inject_include_dir = True

            with generated_file(build, self.env, options.pch_source) as out:
                out.write('#include "{}"\n'.format(header.path.basename()))

    def _create_pch(self, header):
        return ['/Yc' + header.path.suffix]

    def flags(self, options, output):
        syntax = getattr(options, 'syntax', 'msvc')
        header = getattr(options, 'file', None)
        flags = []
        if getattr(options, 'inject_include_dir', False):
            # Add the include path for the generated header; see pre_build()
            # above for more details.
            d = Directory(header.path.parent(), None)
            flags.extend(self._include_dir(d, syntax))

        flags.extend(MsvcBaseCompiler.flags(self, options, output) +
                    (self._create_pch(header) if header else []))
        return flags

    def output_file(self, name, options):
        pchpath = Path(name).stripext('.pch')
        objpath = options.pch_source.path.stripext('.obj').reroot()
        output = MsvcPrecompiledHeader(
            pchpath, objpath, name, self.builder.object_format, self.lang
        )
        if options.pch:
            output.extra_objects = [options.pch.object_file]
        return [output, output.object_file]


class MsvcLinker(BuildCommand):
    flags_var = 'ldflags'
    libs_var = 'ldlibs'

    __lib_re = re.compile(r'(.*)\.lib$')
    __allowed_langs = {
        'c'     : {'c'},
        'c++'   : {'c', 'c++'},
    }

    def __init__(self, builder, env, rule_name, command, ldflags, ldlibs):
        BuildCommand.__init__(
            self, builder, env, rule_name, 'vclink', command,
            flags=('ldflags', ldflags), libs=('ldlibs', ldlibs)
        )

    def _extract_lib_name(self, library):
        basename = library.path.basename()
        m = self.__lib_re.match(basename)
        if not m:
            raise ValueError("'{}' is not a valid library name"
                             .format(basename))
        return m.group(1)

    @property
    def brand(self):
        return self.builder.brand

    @property
    def version(self):
        return self.builder.version

    @property
    def flavor(self):
        return 'msvc'

    def can_link(self, format, langs):
        return (format == self.builder.object_format and
                self.__allowed_langs[self.lang].issuperset(langs))

    @property
    def has_link_macros(self):
        return True

    def search_dirs(self, strict=False):
        lib_path = [os.path.abspath(i) for i in
                    self.env.getvar('LIBRARY_PATH', '').split(os.pathsep)]
        lib = [os.path.abspath(i) for i in
               self.env.getvar('LIB', '').split(os.pathsep)]
        return lib_path + lib

    @property
    def num_outputs(self):
        return 1

    def _call(self, cmd, input, output, libs=None, flags=None):
        return list(chain(
            cmd, self._always_flags, iterate(flags), iterate(input),
            iterate(libs), ['/OUT:' + output]
        ))

    @property
    def _always_flags(self):
        return ['/nologo']

    def _lib_dirs(self, libraries, extra_dirs, syntax):
        dirs = uniques(chain(
            (i.path.parent() for i in iterate(libraries)),
            extra_dirs
        ))
        prefix = '-L' if syntax == 'cc' else '/LIBPATH:'
        return [prefix + i for i in dirs]

    def flags(self, options, output, pkg=False):
        syntax = getattr(options, 'syntax', 'msvc')
        libraries = getattr(options, 'libs', [])
        lib_dirs = getattr(options, 'lib_dirs', [])
        return self._lib_dirs(libraries, lib_dirs, syntax)

    def parse_flags(self, flags):
        parser = ArgumentParser()
        parser.add('/nologo')

        result, extra = parser.parse_known(flags)
        result['extra'] = extra
        return result

    def _link_lib(self, library, syntax):
        if isinstance(library, WholeArchive):
            raise TypeError('MSVC does not support whole-archives')
        if isinstance(library, Framework):
            raise TypeError('MSVC does not support frameworks')

        if syntax == 'cc':
            return ['-l' + self._extract_lib_name(library)]
        else:
            return [library.path.basename()]

    def always_libs(self, primary):
        return []

    def libs(self, options, output, pkg=False):
        syntax = getattr(options, 'syntax', 'msvc')
        libraries = getattr(options, 'libs', [])
        return sum((self._link_lib(i, syntax) for i in libraries), [])


class MsvcExecutableLinker(MsvcLinker):
    def __init__(self, builder, env, command, ldflags, ldlibs):
        MsvcLinker.__init__(self, builder, env, 'vclink', command, ldflags,
                            ldlibs)

    def output_file(self, name, options):
        path = Path(name + self.env.platform.executable_ext)
        return Executable(path, self.builder.object_format, self.lang)


class MsvcSharedLibraryLinker(MsvcLinker):
    def __init__(self, builder, env, command, ldflags, ldlibs):
        MsvcLinker.__init__(self, builder, env, 'vclinklib', command, ldflags,
                            ldlibs)

    @property
    def num_outputs(self):
        return 2

    def _call(self, cmd, input, output, libs=None, flags=None):
        result = MsvcLinker._call(self, cmd, input, output[0], libs, flags)
        result.append('/IMPLIB:' + output[1])
        return result

    def output_file(self, name, options):
        dllname = Path(name + self.env.platform.shared_library_ext)
        impname = Path(name + '.lib')
        expname = Path(name + '.exp')
        dll = DllBinary(dllname, self.builder.object_format, self.lang,
                        impname, expname)
        return [dll, dll.import_lib, dll.export_file]

    @property
    def _always_flags(self):
        return MsvcLinker._always_flags.fget(self) + ['/DLL']


class MsvcStaticLinker(BuildCommand):
    def __init__(self, builder, env, command):
        global_flags = shell.split(env.getvar('LIBFLAGS', ''))
        BuildCommand.__init__(self, builder, env, 'vclib', 'vclib', command,
                              flags=('libflags', global_flags))

    @property
    def flavor(self):
        return 'msvc'

    def can_link(self, format, langs):
        return format == self.builder.object_format

    @property
    def has_link_macros(self):
        return True

    def _call(self, cmd, input, output, flags=None):
        return list(chain(
            cmd, iterate(flags), iterate(input), ['/OUT:' + output]
        ))

    def output_file(self, name, options):
        return StaticLibrary(Path(name + '.lib'),
                             self.builder.object_format, options.langs)

    def parse_flags(self, flags):
        return {'other': flags}


class MsvcPackageResolver(object):
    def __init__(self, builder, env):
        self.builder = builder
        self.env = env

        self.include_dirs = [i for i in uniques(chain(
            self.builder.compiler.search_dirs(), self.env.platform.include_dirs
        )) if os.path.exists(i)]

        self.lib_dirs = [i for i in uniques(chain(
            self.builder.linker('executable').search_dirs(),
            self.env.platform.lib_dirs
        )) if os.path.exists(i)]

    @property
    def lang(self):
        return self.builder.lang

    def header(self, name, search_dirs=None):
        if search_dirs is None:
            search_dirs = self.include_dirs

        for base in search_dirs:
            if os.path.exists(os.path.join(base, name)):
                return HeaderDirectory(Path(base, Root.absolute), None,
                                       system=True, external=True)

        raise PackageResolutionError("unable to find header '{}'".format(name))

    def library(self, name, kind=PackageKind.any, search_dirs=None):
        if search_dirs is None:
            search_dirs = self.lib_dirs
        libname = name + '.lib'

        for base in search_dirs:
            fullpath = os.path.join(base, libname)
            if os.path.exists(fullpath):
                # We don't actually know what kind of library this is. It could
                # be a static library or an import library (which we classify
                # as a kind of shared lib).
                return Library(Path(fullpath, Root.absolute),
                               self.builder.object_format, external=True)
        raise PackageResolutionError("unable to find library '{}'"
                                     .format(name))

    def resolve(self, name, version, kind, headers, lib_names):
        format = self.builder.object_format
        try:
            return pkg_config.resolve(self.env, name, format, version, kind)
        except (OSError, PackageResolutionError):
            if lib_names is default_sentinel:
                lib_names = self.env.platform.transform_package(name)
            includes = [self.header(i) for i in iterate(headers)]
            libs = [self.library(i, kind) for i in iterate(lib_names)]
            return CommonPackage(name, format, includes=includes, libs=libs)
