import os.path
import re
from itertools import chain

from . import pkg_config
from .common import BuildCommand, Builder, check_which, library_macro
from .. import options as opts, safe_str, shell
from ..arguments.windows import ArgumentParser
from ..builtins.file_types import make_immediate_file
from ..exceptions import PackageResolutionError
from ..file_types import *
from ..iterutils import (default_sentinel, iterate, listify, merge_into_dict,
                         uniques)
from ..languages import known_langs, known_formats
from ..objutils import memoize
from ..packages import CommonPackage, Framework, PackageKind
from ..path import abspath, exists, Path, Root
from ..versioning import detect_version, SpecifierSet

_warning_flags = {
    opts.WarningValue.disable: '/w',
    opts.WarningValue.all    : '/W3',
    opts.WarningValue.extra  : '/W4',
    opts.WarningValue.error  : '/WX',
}

_optimize_flags = {
    opts.OptimizeValue.disable : '/Od',
    opts.OptimizeValue.size    : '/O1',
    opts.OptimizeValue.speed   : '/O2',
    opts.OptimizeValue.linktime: '/GL',
}


class MsvcBuilder(Builder):
    def __init__(self, env, langinfo, command, version_output):
        Builder.__init__(self, langinfo.name,
                         *self._parse_brand(version_output))
        self.object_format = env.target_platform.object_format

        name = langinfo.var('compiler').lower()
        ldinfo = known_formats['native', 'dynamic']
        arinfo = known_formats['native', 'static']

        # Look for the last argument that looks like our compiler and use its
        # directory as the base directory to find the linkers.
        origin = ''
        for i in reversed(command):
            if os.path.basename(i) in ('cl', 'cl.exe'):
                origin = os.path.dirname(i)
        link_command = check_which(
            env.getvar(ldinfo.var('linker'), os.path.join(origin, 'link')),
            env.variables, kind='dynamic linker'.format(self.lang)
        )
        lib_command = check_which(
            env.getvar(arinfo.var('linker'), os.path.join(origin, 'lib')),
            env.variables, kind='static linker'.format(self.lang)
        )

        cflags_name = langinfo.var('flags').lower()
        cflags = (
            shell.split(env.getvar('CPPFLAGS', '')) +
            shell.split(env.getvar(langinfo.var('flags'), ''))
        )

        ld_name = ldinfo.var('linker').lower()
        ldflags_name = ldinfo.var('flags').lower()
        ldflags = shell.split(env.getvar(ldinfo.var('flags'), ''))
        ldlibs_name = ldinfo.var('libs').lower()
        ldlibs = shell.split(env.getvar(ldinfo.var('libs'), ''))

        ar_name = arinfo.var('linker').lower()
        arflags_name = arinfo.var('flags').lower()
        arflags = shell.split(env.getvar(arinfo.var('flags'), ''))

        self.compiler = MsvcCompiler(self, env, name, command, cflags_name,
                                     cflags)
        self.pch_compiler = MsvcPchCompiler(self, env, name, command,
                                            cflags_name, cflags)
        self._linkers = {
            'executable': MsvcExecutableLinker(
                self, env, name, ld_name, link_command, ldflags_name, ldflags,
                ldlibs_name, ldlibs
            ),
            'shared_library': MsvcSharedLibraryLinker(
                self, env, name, ld_name, link_command, ldflags_name, ldflags,
                ldlibs_name, ldlibs
            ),
            'static_library': MsvcStaticLinker(
                self, env, ar_name, lib_command, arflags_name, arflags
            ),
        }
        self.packages = MsvcPackageResolver(self, env)
        self.runner = None

    @staticmethod
    def _parse_brand(version_output):
        if 'Microsoft (R)' in version_output:
            return 'msvc', detect_version(version_output)
        # XXX: Detect clang-cl.
        return 'unknown', None

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
    def deps_flavor(self):
        return 'msvc'

    @property
    def needs_libs(self):
        return False

    def search_dirs(self, strict=False):
        cpath = [abspath(i) for i in
                 self.env.getvar('CPATH', '').split(os.pathsep)]
        include = [abspath(i) for i in
                   self.env.getvar('INCLUDE', '').split(os.pathsep)]
        return cpath + include

    def _call(self, cmd, input, output, deps=None, flags=None):
        result = list(chain( cmd, self._always_flags, iterate(flags) ))
        if deps:
            result.append('/showIncludes')
        result.extend(['/c', input, '/Fo' + output])
        return result

    @property
    def _always_flags(self):
        return ['/nologo', '/EHsc']

    def flags(self, options, output=None, mode='normal'):
        syntax = 'cc' if mode == 'pkg-config' else 'msvc'
        flags = []
        for i in options:
            if isinstance(i, opts.include_dir):
                prefix = '-I' if syntax == 'cc' else '/I'
                flags.append(prefix + i.directory.path)
            elif isinstance(i, opts.define):
                prefix = '-D' if syntax == 'cc' else '/D'
                if i.value:
                    flags.append(prefix + i.name + '=' + i.value)
                else:
                    flags.append(prefix + i.name)
            elif isinstance(i, opts.std):
                flags.append('/std:' + i.value)
            elif isinstance(i, opts.warning):
                for j in i.value:
                    flags.append(_warning_flags[j])
            elif isinstance(i, opts.debug):
                flags.append('/Zi')
            elif isinstance(i, opts.optimize):
                for j in i.value:
                    flags.append(_optimize_flags[j])
            elif isinstance(i, opts.pch):
                flags.append('/Yu' + i.header.header_name)
            elif isinstance(i, opts.sanitize):
                flags.append('/RTC1')
            elif isinstance(i, safe_str.stringy_types):
                flags.append(i)
            else:
                raise TypeError('unknown option type {!r}'.format(type(i)))
        return flags

    @staticmethod
    @memoize
    def __parser():
        parser = ArgumentParser()
        parser.add('/nologo')
        parser.add('/D', '-D', type=list, dest='defines')
        parser.add('/I', '-I', type=list, dest='includes')

        warn = parser.add('/W', type=dict, dest='warnings')
        warn.add('0', '1', '2', '3', '4', 'all', dest='level')
        warn.add('X', type=bool, dest='as_error')
        warn.add('X-', type=bool, dest='as_error', value=False)
        parser.add('/w', type='alias', base=warn, value='0')

        pch = parser.add('/Y', type=dict, dest='pch')
        pch.add('u', type=str, dest='use')
        pch.add('c', type=str, dest='create')

        return parser

    def parse_flags(self, flags):
        result, extra = self.__parser().parse_known(flags)
        result['extra'] = extra
        return result


class MsvcCompiler(MsvcBaseCompiler):
    def __init__(self, builder, env, name, command, cflags_name, cflags):
        MsvcBaseCompiler.__init__(self, builder, env, name, name, command,
                                  cflags_name, cflags)

    @property
    def accepts_pch(self):
        return True

    def default_name(self, input, context):
        return input.path.stripext().suffix

    def output_file(self, name, context):
        pch = getattr(context, 'pch', None)
        output = ObjectFile(Path(name + '.obj'),
                            self.builder.object_format, self.lang)
        if pch:
            output.extra_objects = [pch.object_file]
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

    def pre_build(self, build, name, context):
        header = getattr(context, 'file')
        options = opts.option_list()

        if context.pch_source is None:
            ext = known_langs[self.lang].default_ext('source')
            context.pch_source = SourceFile(header.path.stripext(ext).reroot(),
                                            header.lang)
            with make_immediate_file(build, self.env, context.pch_source) \
                 as out:  # noqa
                out.write('#include "{}"\n'.format(header.path.basename()))

            # Add the include path for the header to ensure the PCH source
            # finds it.
            d = HeaderDirectory(header.path.parent())
            options.append(opts.include_dir(d))

        # Add flag to create PCH file.
        options.append('/Yc' + header.path.suffix)
        return options

    def default_name(self, input, context):
        return input.path.suffix

    def output_file(self, name, context):
        pchpath = Path(name).stripext('.pch')
        objpath = context.pch_source.path.stripext('.obj').reroot()
        output = MsvcPrecompiledHeader(
            pchpath, objpath, name, self.builder.object_format, self.lang
        )
        return [output, output.object_file]


class MsvcLinker(BuildCommand):
    __lib_re = re.compile(r'(.*)\.lib$')
    __allowed_langs = {
        'c'     : {'c'},
        'c++'   : {'c', 'c++'},
    }

    def __init__(self, builder, env, rule_name, name, command, ldflags_name,
                 ldflags, ldlibs_name, ldlibs):
        BuildCommand.__init__(
            self, builder, env, rule_name, name, command,
            flags=(ldflags_name, ldflags), libs=(ldlibs_name, ldlibs)
        )

    def _extract_lib_name(self, library):
        basename = library.path.basename()
        m = self.__lib_re.match(basename)
        if not m:
            raise ValueError("'{}' is not a valid library name"
                             .format(basename))
        return m.group(1)

    def can_link(self, format, langs):
        return (format == self.builder.object_format and
                self.__allowed_langs[self.lang].issuperset(langs))

    @property
    def needs_libs(self):
        return True

    @property
    def has_link_macros(self):
        return True

    def search_dirs(self, strict=False):
        lib_path = [abspath(i) for i in
                    self.env.getvar('LIBRARY_PATH', '').split(os.pathsep)]
        lib = [abspath(i) for i in
               self.env.getvar('LIB', '').split(os.pathsep)]
        return lib_path + lib

    def _call(self, cmd, input, output, libs=None, flags=None):
        return list(chain(
            cmd, self._always_flags, iterate(flags), iterate(input),
            iterate(libs), ['/OUT:' + output]
        ))

    @property
    def _always_flags(self):
        return ['/nologo']

    def always_libs(self, primary):
        return opts.option_list()

    def _link_lib(self, library, syntax):
        if isinstance(library, Framework):
            raise TypeError('MSVC does not support frameworks')
        elif isinstance(library, WholeArchive):
            if not self.version or self.version in SpecifierSet('>=19'):
                return ['/WHOLEARCHIVE:' + library.path]
            raise TypeError('whole-archives require MSVC 2015 Update 2')

        # Unlike the cc linker, we only support Library objects here (strings
        # aren't allowed!)
        if syntax == 'cc':
            return ['-l' + self._extract_lib_name(library)]
        else:
            # Pass the raw path to the library. We do this to avoid adding more
            # `/LIBPATH` options than we really need, which makes it easier to
            # find the right library when there are name collisions (e.g.
            # linking to a system `libfoo` when also building a local `libfoo`
            # to use elsewhere).
            return [library.path]

    def _lib_dir(self, library, syntax):
        if syntax == 'cc' and not isinstance(library, WholeArchive):
            return [library.path.parent()]
        return []

    def flags(self, options, output=None, mode='normal'):
        syntax = 'cc' if mode == 'pkg-config' else 'msvc'
        flags, lib_dirs = [], []
        for i in options:
            if isinstance(i, opts.lib_dir):
                lib_dirs.append(i.directory.path)
            elif isinstance(i, opts.lib):
                lib_dirs.extend(self._lib_dir(i.library, syntax))
            elif isinstance(i, opts.module_def):
                flags.append('/DEF:' + i.value.path)
            elif isinstance(i, opts.debug):
                flags.append('/DEBUG')
            elif isinstance(i, opts.optimize):
                if opts.OptimizeValue.linktime in i.value:
                    flags.append('/LTCG')
            elif isinstance(i, safe_str.stringy_types):
                flags.append(i)
            elif isinstance(i, opts.lib_literal):
                pass
            else:
                raise TypeError('unknown option type {!r}'.format(type(i)))

        prefix = '-L' if syntax == 'cc' else '/LIBPATH:'
        flags.extend(prefix + i for i in uniques(lib_dirs))
        return flags

    def lib_flags(self, options, mode='normal'):
        syntax = 'cc' if mode == 'pkg-config' else 'msvc'
        flags = []
        for i in options:
            if isinstance(i, opts.lib):
                flags.extend(self._link_lib(i.library, syntax))
            elif isinstance(i, opts.lib_literal):
                flags.append(i.value)
        return flags

    @staticmethod
    @memoize
    def __parser():
        parser = ArgumentParser()
        parser.add('/nologo')
        return parser

    @staticmethod
    @memoize
    def __lib_parser():
        parser = ArgumentParser()
        parser.add('/nologo')
        parser.add_unnamed('libs')
        return parser

    def parse_flags(self, flags, lib_flags):
        result, extra = self.__parser().parse_known(flags)
        libresult, libextra = self.__lib_parser().parse_known(lib_flags)

        merge_into_dict(result, libresult)
        result['extra'] = extra + libextra
        return result


class MsvcExecutableLinker(MsvcLinker):
    def __init__(self, builder, env, name, command_var, command, ldflags_name,
                 ldflags, ldlibs_name, ldlibs):
        MsvcLinker.__init__(self, builder, env, name + '_link', command_var,
                            command, ldflags_name, ldflags, ldlibs_name,
                            ldlibs)

    def output_file(self, name, context):
        path = Path(name + self.env.target_platform.executable_ext)
        return Executable(path, self.builder.object_format, self.lang)


class MsvcSharedLibraryLinker(MsvcLinker):
    def __init__(self, builder, env, name, command_var, command, ldflags_name,
                 ldflags, ldlibs_name, ldlibs):
        MsvcLinker.__init__(self, builder, env, name + '_linklib', command_var,
                            command, ldflags_name, ldflags, ldlibs_name,
                            ldlibs)

    @property
    def num_outputs(self):
        return 2

    def _call(self, cmd, input, output, libs=None, flags=None):
        result = MsvcLinker._call(self, cmd, input, output[0], libs, flags)
        result.append('/IMPLIB:' + output[1])
        return result

    @property
    def _always_flags(self):
        return MsvcLinker._always_flags.fget(self) + ['/DLL']

    def compile_options(self, context):
        options = opts.option_list()
        if self.has_link_macros:
            options.append(opts.define(library_macro(
                context.name, 'shared_library'
            )))
        return options

    def output_file(self, name, context):
        dllname = Path(name + self.env.target_platform.shared_library_ext)
        impname = Path(name + '.lib')
        expname = Path(name + '.exp')
        dll = DllBinary(dllname, self.builder.object_format, self.lang,
                        impname, expname)
        return [dll, dll.import_lib, dll.export_file]


class MsvcStaticLinker(BuildCommand):
    def __init__(self, builder, env, name, command, arflags_name, arflags):
        BuildCommand.__init__(self, builder, env, name, name,
                              command, flags=(arflags_name, arflags))

    def can_link(self, format, langs):
        return format == self.builder.object_format

    @property
    def has_link_macros(self):
        return True

    def _call(self, cmd, input, output, flags=None):
        return list(chain(
            cmd, iterate(flags), iterate(input), ['/OUT:' + output]
        ))

    def compile_options(self, context):
        return self.forwarded_compile_options(context)

    def forwarded_compile_options(self, context):
        options = opts.option_list()
        if self.has_link_macros:
            options.append(opts.define(library_macro(
                context.name, 'static_library'
            )))
        return options

    def flags(self, options, output=None, mode='normal'):
        flags = []
        for i in options:
            if isinstance(i, safe_str.stringy_types):
                flags.append(i)
            else:
                raise TypeError('unknown option type {!r}'.format(type(i)))
        return flags

    def output_file(self, name, context):
        return StaticLibrary(Path(name + '.lib'),
                             self.builder.object_format, context.langs)

    def parse_flags(self, flags):
        return {'extra': flags}


class MsvcPackageResolver(object):
    def __init__(self, builder, env):
        self.builder = builder
        self.env = env

        self.include_dirs = [i for i in uniques(chain(
            self.builder.compiler.search_dirs(),
            self.env.host_platform.include_dirs
        )) if exists(i)]

        self.lib_dirs = [i for i in uniques(chain(
            self.builder.linker('executable').search_dirs(),
            self.env.host_platform.lib_dirs
        )) if exists(i)]

    @property
    def lang(self):
        return self.builder.lang

    def header(self, name, search_dirs=None):
        if search_dirs is None:
            search_dirs = self.include_dirs

        for base in search_dirs:
            if base.root != Root.absolute:
                raise ValueError('expected an absolute path')
            if exists(base.append(name)):
                return HeaderDirectory(base, None, system=True)

        raise PackageResolutionError("unable to find header '{}'".format(name))

    def library(self, name, kind=PackageKind.any, search_dirs=None):
        if search_dirs is None:
            search_dirs = self.lib_dirs
        libname = name + '.lib'

        for base in search_dirs:
            if base.root != Root.absolute:
                raise ValueError('expected an absolute path')
            fullpath = base.append(libname)
            if exists(fullpath):
                # We don't actually know what kind of library this is. It could
                # be a static library or an import library (which we classify
                # as a kind of shared lib).
                return Library(fullpath, self.builder.object_format)
        raise PackageResolutionError("unable to find library '{}'"
                                     .format(name))

    def resolve(self, name, version, kind, headers, lib_names):
        format = self.builder.object_format
        try:
            return pkg_config.resolve(self.env, name, format, version, kind)
        except (OSError, PackageResolutionError):
            if lib_names is default_sentinel:
                lib_names = self.env.target_platform.transform_package(name)

            compile_options = opts.option_list(
                opts.include_dir(self.header(i)) for i in iterate(headers)
            )
            link_options = opts.option_list(
                opts.lib(self.library(i, kind)) for i in iterate(lib_names)
            )
            return CommonPackage(name, format, compile_options, link_options)
