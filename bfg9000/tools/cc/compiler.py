from itertools import chain

from ... import options as opts, safe_str, shell
from .flags import optimize_flags
from ..common import BuildCommand
from ...file_types import ObjectFile, PrecompiledHeader
from ...iterutils import default_sentinel, iterate
from ...objutils import memoize_method
from ...path import abspath, Path
from ...versioning import SpecifierSet


class CcBaseCompiler(BuildCommand):
    @property
    def deps_flavor(self):
        return None if self.lang in ('f77', 'f95') else 'gcc'

    @property
    def needs_libs(self):
        return False

    @property
    def needs_package_options(self):
        return True

    @memoize_method
    def _search_dirs(self, cpath=default_sentinel, strict=False):
        try:
            extra_env = ({'CPATH': cpath or ''}
                         if cpath is not default_sentinel else None)
            output = self.env.execute(
                (self.command + self._always_flags + self.global_flags +
                 ['-E', '-Wp,-v', '/dev/null']),
                extra_env=extra_env, stdout=shell.Mode.pipe,
                stderr=shell.Mode.stdout
            )

            found = False
            dirs = []
            for i in output.splitlines():  # pragma: no branch
                if i == '#include <...> search starts here:':
                    found = True
                elif i == 'End of search list.':
                    break
                elif i[0] != ' ':
                    found = False
                elif found:
                    dirs.append(abspath(i[1:]))
            return dirs
        except (OSError, shell.CalledProcessError):
            if strict:
                raise
            return self.env.variables.getpaths('CPATH')

    def search_dirs(self, strict=False):
        return self._search_dirs(strict=strict)

    def _call(self, cmd, input, output, deps=None, flags=None):
        result = list(chain(
            cmd, self._always_flags, iterate(flags), ['-c', input]
        ))
        if deps:
            result.extend(['-MMD', '-MF', deps])
        result.extend(['-o', output])
        return result

    @property
    def _always_flags(self):
        flags = ['-x', self._langs[self.lang]]
        # Force color diagnostics on Ninja, since it's off by default. See
        # <https://github.com/ninja-build/ninja/issues/174> for more
        # information.
        if self.env.backend == 'ninja':
            if self.brand == 'clang':
                flags.append('-fcolor-diagnostics')
            elif (self.brand == 'gcc' and self.version and
                  self.version in SpecifierSet('>=4.9')):
                flags.append('-fdiagnostics-color')
        return flags

    def _include_dir(self, directory, allow_system):
        default_dirs = self._search_dirs(None)
        if directory.path in default_dirs:
            # Don't include default directories (e.g. /usr/include). Including
            # them as system dirs would break GCC 6 when #including stdlib.h:
            # <https://gcc.gnu.org/bugzilla/show_bug.cgi?id=70129>. Including
            # them as regular directories isn't right either.
            return []
        elif allow_system and directory.system:
            return ['-isystem', directory.path]
        else:
            return ['-I' + directory.path]

    def flags(self, options, global_options=None, output=None, mode='normal'):
        pkgconf_mode = mode == 'pkg-config'
        flags = []
        for i in options:
            if isinstance(i, opts.include_dir):
                flags.extend(self._include_dir(i.directory, not pkgconf_mode))
            elif isinstance(i, opts.define):
                if i.value:
                    flags.append('-D' + i.name + '=' + i.value)
                else:
                    flags.append('-D' + i.name)
            elif isinstance(i, opts.std):
                flags.append('-std=' + i.value)
            elif isinstance(i, opts.warning):
                for j in i.value:
                    if j == opts.WarningValue.disable:
                        flags.append('-w')
                    else:
                        flags.append('-W' + j.name)
            elif isinstance(i, opts.debug):
                flags.append('-g')
            elif isinstance(i, opts.static):
                pass
            elif isinstance(i, opts.optimize):
                for j in i.value:
                    flags.append(optimize_flags[j])
            elif isinstance(i, opts.pthread):
                flags.append('-pthread')
            elif isinstance(i, opts.pic):
                flags.append('-fPIC')
            elif isinstance(i, opts.pch):
                flags.extend(['-include', i.header.path.stripext()])
            elif isinstance(i, opts.sanitize):
                flags.append('-fsanitize=address')
            elif isinstance(i, safe_str.stringy_types):
                flags.append(i)
            else:
                raise TypeError('unknown option type {!r}'.format(type(i)))
        return flags


class CcCompiler(CcBaseCompiler):
    _langs = {
        'c'     : 'c',
        'c++'   : 'c++',
        'objc'  : 'objective-c',
        'objc++': 'objective-c++',
        'f77'   : 'f77',
        'f95'   : 'f95',
        'java'  : 'java',
    }

    def __init__(self, builder, env, *, command, flags):
        super().__init__(builder, env, command=command, flags=flags)

    @property
    def accepts_pch(self):
        return True

    def default_name(self, input, step):
        return input.path.stripext().suffix

    def output_file(self, name, step):
        # XXX: MinGW's object format doesn't appear to be COFF...
        return ObjectFile(Path(name + '.o'), self.builder.object_format,
                          self.lang)


class CcPchCompiler(CcBaseCompiler):
    _langs = {
        'c'     : 'c-header',
        'c++'   : 'c++-header',
        'objc'  : 'objective-c-header',
        'objc++': 'objective-c++-header',
    }

    def __init__(self, builder, env, *, command, flags):
        if builder.lang not in self._langs:
            raise ValueError('{} has no precompiled headers'
                             .format(builder.lang))
        super().__init__(builder, env, command[0] + '_pch', command=command,
                         flags=flags)

    @property
    def accepts_pch(self):
        # You can't pass a PCH to a PCH compiler!
        return False

    def default_name(self, input, step):
        return input.path.suffix

    def output_file(self, name, step):
        ext = '.gch' if self.brand == 'gcc' else '.pch'
        return PrecompiledHeader(Path(name + ext), self.lang)
