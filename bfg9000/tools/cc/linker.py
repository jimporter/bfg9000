import re
from functools import partial
from itertools import chain

from .. import install_name_tool, patchelf
from ... import options as opts, safe_str, shell
from .flags import optimize_flags
from ..common import BuildCommand, library_macro
from ...builtins.copy_file import CopyFile
from ...file_types import *
from ...iterutils import first, iterate, listify, recursive_walk, uniques
from ...path import abspath, Path
from ...versioning import SpecifierSet
from ...packages import Framework


class CcLinker(BuildCommand):
    __known_langs = {'java', 'c', 'c++', 'objc', 'objc++', 'f77', 'f95'}
    __allowed_langs = {
        'c'     : {'c'},
        'c++'   : {'c', 'c++', 'f77', 'f95'},
        'objc'  : {'c', 'objc', 'f77', 'f95'},
        'objc++': {'c', 'c++', 'objc', 'objc++', 'f77', 'f95'},
        'f77'   : {'c', 'f77', 'f95'},
        'f95'   : {'c', 'f77', 'f95'},
        'java'  : {'java', 'c', 'c++', 'objc', 'objc++', 'f77', 'f95'},
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create a regular expression to extract the library name for linking
        # with -l.
        lib_formats = [r'lib(.*)\.a']
        if not self.env.target_platform.has_import_library:
            so_ext = re.escape(self.env.target_platform.shared_library_ext)
            lib_formats.append(r'lib(.*)' + so_ext)
        if self.env.target_platform.family == 'windows':
            lib_formats.append(r'(.*)\.lib')
        self._lib_re = re.compile('(?:' + '|'.join(lib_formats) + ')$')

    def _extract_lib_name(self, library):
        basename = library.path.basename()
        m = self._lib_re.match(basename)
        if not m:
            raise ValueError("'{}' is not a valid library name"
                             .format(basename))

        # Get the first non-None group from the match.
        return next(i for i in m.groups() if i is not None)

    def can_link(self, format, langs):
        if format != self.builder.object_format:
            return False
        relevant_langs = self.__known_langs.intersection(langs)
        return self.__allowed_langs[self.lang].issuperset(relevant_langs)

    @property
    def needs_libs(self):
        return True

    @property
    def needs_package_options(self):
        return True

    @property
    def _has_link_macros(self):
        # We only need to define LIBFOO_EXPORTS/LIBFOO_STATIC macros on
        # platforms that have different import/export rules for libraries. We
        # approximate this by checking if the platform uses import libraries,
        # and only define the macros if it does.
        return self.env.target_platform.has_import_library

    def sysroot(self, strict=False):
        try:
            # XXX: clang doesn't support -print-sysroot.
            return self.env.execute(
                self.command + self.global_flags + ['-print-sysroot'],
                stdout=shell.Mode.pipe, stderr=shell.Mode.devnull
            ).rstrip()
        except (OSError, shell.CalledProcessError):
            if strict:
                raise
            return '' if self.env.target_platform.family == 'windows' else '/'

    def search_dirs(self, strict=False):
        try:
            output = self.env.execute(
                self.command + self.global_flags + ['-print-search-dirs'],
                stdout=shell.Mode.pipe, stderr=shell.Mode.devnull
            )
            m = re.search(r'^libraries: =(.*)', output, re.MULTILINE)
            search_dirs = [abspath(i) for i in shell.split_paths(m.group(1))]

            # clang doesn't respect LIBRARY_PATH with -print-search-dirs;
            # see <https://bugs.llvm.org//show_bug.cgi?id=23877>.
            if self.brand == 'clang':
                search_dirs = (self.env.variables.getpaths('LIBRARY_PATH') +
                               search_dirs)
        except (OSError, shell.CalledProcessError):
            if strict:
                raise
            search_dirs = self.env.variables.getpaths('LIBRARY_PATH')
        return search_dirs

    def _call(self, cmd, input, output, libs=None, flags=None):
        return list(chain(
            cmd, self._always_flags, iterate(flags), iterate(input),
            iterate(libs), ['-o', output]
        ))

    @property
    def _always_flags(self):
        if self.builder.object_format == 'mach-o':
            return ['-Wl,-headerpad_max_install_names']
        return []

    def _local_rpath(self, library, output):
        if ( not isinstance(library, Library) or
             self.builder.object_format != 'elf' ):
            return None, []

        rpath = patchelf.local_rpath(self.env, library, output)
        if rpath is None:
            return None, []

        # Prior to binutils 2.28, GNU's BFD-based ld doesn't correctly respect
        # $ORIGIN in a shared library's DT_RPATH/DT_RUNPATH field. This results
        # in ld being unable to find other shared libraries needed by the
        # directly-linked library. For more information, see:
        # <https://sourceware.org/bugzilla/show_bug.cgi?id=20535>.
        try:
            ld = self.builder.linker('raw')
            fix_rpath = (ld.brand == 'bfd' and ld.version in
                         SpecifierSet('<2.28'))
        except KeyError:
            fix_rpath = False

        rpath_link = []
        if output and fix_rpath:
            rpath_link = [i.path.parent() for i in
                          recursive_walk(library.runtime_file, 'runtime_deps')]

        return rpath, rpath_link

    def always_libs(self, primary):
        # XXX: Don't just asssume that these are the right libraries to use.
        # For instance, clang users might want to use libc++ instead.
        libs = opts.option_list()
        if self.lang in ('c++', 'objc++') and not primary:
            libs.append(opts.lib('stdc++'))
        if self.lang in ('objc', 'objc++') and self.brand == 'gcc':
            libs.append(opts.lib('objc'))
        if self.lang in ('f77', 'f95') and not primary:
            libs.append(opts.lib('gfortran'))
        if self.lang == 'java' and not primary:
            libs.append(opts.lib('gcj'))
        return libs

    def _link_lib(self, library, raw_link):
        def common_link(library):
            return ['-l' + self._extract_lib_name(library)]

        if isinstance(library, WholeArchive):
            if self.env.target_platform.genus == 'darwin':
                return ['-Wl,-force_load', library.path]
            return ['-Wl,--whole-archive', library.path,
                    '-Wl,--no-whole-archive']
        elif isinstance(library, Framework):
            if not self.env.target_platform.has_frameworks:
                raise TypeError('frameworks not supported on this platform')
            return ['-framework', library.full_name]
        elif isinstance(library, str):
            return ['-l' + library]
        elif isinstance(library, SharedLibrary):
            # If we created this library, we know its soname is set, so passing
            # the raw path to the library works (without soname, the linker
            # would create a reference to the absolute path of the library,
            # which we don't want). We do this to avoid adding more `-L`
            # options than we really need, which makes it easier to find the
            # right library when there are name collisions (e.g. linking to a
            # system `libfoo` when also building a local `libfoo` to use
            # elsewhere).
            if raw_link and library.creator:
                return [library.path]
            return common_link(library)
        elif isinstance(library, StaticLibrary):
            # In addition to the reasons above for shared libraries, we pass
            # static libraries in raw form as a way of avoiding getting the
            # shared version when we don't want it. (There are linker options
            # that do this too, but this way is more compatible and fits with
            # what we already do.)
            if raw_link:
                return [library.path]
            return common_link(library)

        # If we get here, we should have a generic `Library` object (probably
        # from MinGW). The naming for these doesn't work with `-l`, but we'll
        # try just in case and back to emitting the path in raw form.
        try:
            return common_link(library)
        except ValueError:
            if raw_link:
                return [library.path]
            raise

    def _lib_dir(self, library, raw_link):
        if not isinstance(library, Library):
            return []
        elif isinstance(library, StaticLibrary):
            return [] if raw_link else [library.path.parent()]
        elif isinstance(library, SharedLibrary):
            return ([] if raw_link and library.creator else
                    [library.path.parent()])

        # As above, if we get here, we should have a generic `Library` object
        # (probably from MinGW). Use `-L` if the library name works with `-l`;
        # otherwise, return nothing, since the library itself will be passed
        # "raw" (like static libraries).
        try:
            self._extract_lib_name(library)
            return [library.path.parent()]
        except ValueError:
            if raw_link:
                return []
            raise

    def flags(self, options, global_options=None, output=None, mode='normal'):
        pkgconf_mode = mode == 'pkg-config'
        flags, rpaths, rpath_links, lib_dirs = [], [], [], []

        for i in options:
            if isinstance(i, opts.lib_dir):
                lib_dirs.append(i.directory.path)
            elif isinstance(i, opts.lib):
                lib_dirs.extend(self._lib_dir(i.library, not pkgconf_mode))
                if not pkgconf_mode:
                    rp, rplink = self._local_rpath(i.library, output)
                    rpaths.extend(iterate(rp))
                    rpath_links.extend(rplink)
            elif isinstance(i, opts.rpath_dir):
                if not pkgconf_mode and i.when & opts.RpathWhen.uninstalled:
                    rpaths.append(i.path)
            elif isinstance(i, opts.rpath_link_dir):
                if not pkgconf_mode:
                    rpath_links.append(i.path)
            elif isinstance(i, opts.module_def):
                if self.env.target_platform.has_import_library:
                    flags.append(i.value.path)
            elif isinstance(i, opts.debug):
                flags.append('-g')
            elif isinstance(i, opts.static):
                flags.append('-static')
            elif isinstance(i, opts.optimize):
                for j in i.value:
                    flags.append(optimize_flags[j])
            elif isinstance(i, opts.pthread):
                # macOS doesn't expect -pthread when linking.
                if self.env.target_platform.genus != 'darwin':
                    flags.append('-pthread')
            elif isinstance(i, opts.entry_point):
                if self.lang == 'java':
                    flags.append('--main={}'.format(i.value))
                else:
                    flags.append('-Wl,-e,{}'.format(i.value))
            elif isinstance(i, safe_str.stringy_types):
                flags.append(i)
            elif isinstance(i, opts.gui):
                if self.env.target_platform.family == 'windows':
                    flags.append('-mwindows')
            elif isinstance(i, opts.install_name_change):
                pass
            elif isinstance(i, opts.lib_literal):
                pass
            else:
                raise TypeError('unknown option type {!r}'.format(type(i)))

        flags.extend('-L' + i for i in uniques(lib_dirs))
        if rpaths:
            flags.append('-Wl,-rpath,' + safe_str.join(rpaths, ':'))
        if rpath_links:
            flags.append('-Wl,-rpath-link,' + safe_str.join(rpath_links, ':'))
        return flags

    def lib_flags(self, options, global_options=None, mode='normal'):
        pkgconf_mode = mode == 'pkg-config'
        flags = []
        for i in options:
            if isinstance(i, opts.lib):
                flags.extend(self._link_lib(i.library, not pkgconf_mode))
            elif isinstance(i, opts.lib_literal):
                flags.append(i.value)
        return flags

    def post_install(self, options, output, step):
        if self.builder.object_format not in ['elf', 'mach-o']:
            return None

        if self.builder.object_format == 'elf':
            return partial(patchelf.post_install, self.env, options, output)
        else:  # mach-o
            return partial(install_name_tool.post_install, self.env,
                           options, output, is_library=self._is_library)


class CcExecutableLinker(CcLinker):
    _is_library = False

    def __init__(self, builder, env, *, command, flags, libs):
        super().__init__(builder, env, command[0] + '_link', command=command,
                         flags=flags, libs=libs)

    def output_file(self, name, step):
        path = Path(name + self.env.target_platform.executable_ext)
        return Executable(path, self.builder.object_format, self.lang)


class CcSharedLibraryLinker(CcLinker):
    _is_library = True

    def __init__(self, builder, env, *, command, flags, libs):
        super().__init__(builder, env, command[0] + '_linklib',
                         command=command, flags=flags, libs=libs)

    @property
    def num_outputs(self):
        return 2 if self.env.target_platform.has_import_library else 'all'

    def _call(self, cmd, input, output, libs=None, flags=None):
        output = listify(output)
        result = super()._call(cmd, input, output[0], libs, flags)
        if self.env.target_platform.has_import_library:
            result.append('-Wl,--out-implib=' + output[1])
        return result

    def _lib_name(self, name, prefix='lib', suffix=''):
        head, tail = Path(name).splitleaf()
        ext = self.env.target_platform.shared_library_ext
        return head.append(prefix + tail + ext + suffix)

    def post_output(self, context, options, output, step):
        if isinstance(output, VersionedSharedLibrary):
            # Make symlinks for the various versions of the shared lib.
            CopyFile(context, output.soname, output, mode='symlink')
            CopyFile(context, output.link, output.soname, mode='symlink')
            return output.link

    def output_file(self, name, step):
        version = getattr(step, 'version', None)
        soversion = getattr(step, 'soversion', None)
        fmt = self.builder.object_format

        if version and self.env.target_platform.has_versioned_library:
            if self.env.target_platform.genus == 'darwin':
                real = self._lib_name(name + '.{}'.format(version))
                soname = self._lib_name(name + '.{}'.format(soversion))
            else:
                real = self._lib_name(name, suffix='.{}'.format(version))
                soname = self._lib_name(name, suffix='.{}'.format(soversion))
            link = self._lib_name(name)
            return VersionedSharedLibrary(real, fmt, self.lang, soname, link)
        elif self.env.target_platform.has_import_library:
            dllprefix = ('cyg' if self.env.target_platform.genus == 'cygwin'
                         else '')
            dllname = self._lib_name(name, prefix=dllprefix)
            impname = self._lib_name(name, suffix='.a')
            dll = DllBinary(dllname, fmt, self.lang, impname)
            return [dll, dll.import_lib]
        else:
            return SharedLibrary(self._lib_name(name), fmt, self.lang)

    @property
    def _always_flags(self):
        shared = ('-dynamiclib' if self.env.target_platform.genus == 'darwin'
                  else '-shared')
        return super()._always_flags + [shared, '-fPIC']

    def _soname(self, library):
        if self.env.target_platform.genus == 'darwin':
            return ['-install_name', install_name_tool.darwin_install_name(
                library, self.env
            )]
        else:
            if isinstance(library, VersionedSharedLibrary):
                soname = library.soname
            else:
                soname = library
            return ['-Wl,-soname,' + soname.path.basename()]

    def compile_options(self, step):
        options = opts.option_list()
        if self.builder.object_format != 'coff':
            options.append(opts.pic())
        if self._has_link_macros:
            options.append(opts.define(
                library_macro(step.name, 'shared_library')
            ))
        return options

    def flags(self, options, global_options=None, output=None, mode='normal'):
        flags = super().flags(options, global_options, output, mode)
        if output:
            flags.extend(self._soname(first(output)))
        return flags
