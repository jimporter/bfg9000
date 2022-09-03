import warnings
from collections import Counter
from itertools import chain

from . import builtin
from .file_types import make_immediate_file
from .install import can_install
from .. import options as opts, path
from ..build_inputs import build_input
from ..file_types import *
from ..iterutils import flatten, iterate, uniques, recursive_walk
from ..objutils import objectify, identity
from ..packages import CommonPackage, Package
from ..safe_str import literal, shell_literal
from ..shell import posix as pshell
from ..shell.syntax import Syntax, Writer
from ..tools.install_name_tool import darwin_install_name
from ..tools.pkg_config import GeneratedPkgConfigPackage, PkgConfigPackage
from ..versioning import simplify_specifiers, Specifier, SpecifierSet

build_input('pkg_config')(lambda build_inputs, env: [])


class Requirement:
    def __init__(self, name, version=None):
        self.name = name
        self.version = objectify(version or '', SpecifierSet)

    def __and__(self, rhs):
        result = Requirement(self.name, self.version)
        result &= rhs
        return result

    def __iand__(self, rhs):
        if self.name != rhs.name:
            raise ValueError('requirement names do not match')
        self.version = self.version & rhs.version
        return self

    def __eq__(self, rhs):
        return (type(self) == type(rhs) and self.name == rhs.name and
                self.version == rhs.version)

    def __ne__(self, rhs):
        return not (self == rhs)

    def split(self, single=False):
        specs = simplify_specifiers(self.version)
        if len(specs) == 0:
            return [SimpleRequirement(self.name)]
        if single and len(specs) > 1:
            raise ValueError(
                ('multiple specifiers ({}) used in pkg-config requirement ' +
                 "for '{}'").format(self.version, self.name)
            )
        return [SimpleRequirement(self.name, i) for i in specs]

    def __hash__(self):
        return hash((self.name, self.version))

    def __repr__(self):
        return '<Requirement({!r})>'.format(self._string())

    def _string(self):  # pragma: no cover
        return self.name + str(self.version)


class SimpleRequirement:
    def __init__(self, name, version=None):
        self.name = name
        self.version = (None if version is None else
                        objectify(version, Specifier))

    def __eq__(self, rhs):
        return (type(self) == type(rhs) and self.name == rhs.name and
                self.version == rhs.version)

    def __ne__(self, rhs):
        return not (self == rhs)

    def _safe_str(self):
        if not self.version:
            return shell_literal(self.name)
        op = self.version.operator
        if op == '==':
            op = '='
        return shell_literal('{name} {op} {version}'.format(
            name=self.name, op=op, version=self.version.version
        ))

    def __hash__(self):
        return hash((self.name, self.version))

    def __repr__(self):
        return '<SimpleRequirement({!r})>'.format(self._string())

    def _string(self):  # pragma: no cover
        return self.name + ('' if self.version is None else str(self.version))


class RequirementSet:
    def __init__(self, iterable=None):
        self._reqs = {}
        if iterable:
            for i in iterable:
                self.add(i)

    def add(self, item):
        if item.name not in self._reqs:
            self._reqs[item.name] = item
        else:
            self._reqs[item.name] &= item

    def remove(self, name):
        del self._reqs[name]

    def update(self, other):
        for i in other:
            self.add(i)

    def merge_from(self, other):
        items = list(other)
        for i in items:
            if i.name in self._reqs:
                self._reqs[i.name] &= i
                other.remove(i.name)

    def split(self, single=False):
        return sorted(flatten(i.split(single) for i in self),
                      key=lambda x: x.name)

    def copy(self):
        return RequirementSet(self)

    def __iter__(self):
        return iter(self._reqs.values())

    def __repr__(self):
        return '<RequirementSet({!r})>'.format(
            [i._string() for i in iter(self)]
        )


class PkgConfigInfo:
    class _simple_property:
        def __init__(self, fn):
            self.fn = fn

        def __get__(self, obj, owner=None):
            if obj is None:
                return self
            return getattr(obj, '_' + self.fn.__name__)

        def __set__(self, obj, value):
            final_value = self.fn(obj, value) if value is not None else None
            setattr(obj, '_' + self.fn.__name__, final_value)

    def __init__(self, context, name=None, *, desc_name=None, desc=None,
                 url=None, version=None, requires=None, requires_private=None,
                 conflicts=None, includes=None, libs=None, libs_private=None,
                 options=None, link_options=None, link_options_private=None,
                 lang=None, auto_fill=False):
        self._builtins = context.builtins
        self.auto_fill = auto_fill

        self.name = name
        self.desc_name = desc_name
        self.desc = desc
        self.url = url
        self.version = version
        self.lang = lang or context.build['project']['lang']

        self._require_deps = []
        self.requires = requires
        self.requires_private = requires_private
        self.conflicts = conflicts

        self.includes = includes
        self.libs = libs
        self.libs_private = libs_private
        self.options = pshell.listify(options, type=opts.option_list)
        self.link_options = pshell.listify(link_options, type=opts.option_list)
        self.link_options_private = pshell.listify(link_options_private,
                                                   type=opts.option_list)

    @_simple_property
    def includes(self, value):
        return uniques(self._header(i) for i in iterate(value))

    @_simple_property
    def libs(self, value):
        return uniques(self._library(i) for i in iterate(value))

    @_simple_property
    def libs_private(self, value):
        return uniques(self._library(i) for i in iterate(value))

    @_simple_property
    def requires(self, value):
        return self._set_requires(value)

    @_simple_property
    def requires_private(self, value):
        return self._set_requires(value)

    @_simple_property
    def conflicts(self, value):
        return self._filter_packages(iterate(value))[0]

    def _header(self, header):
        if not isinstance(header, HeaderFile):
            header = self._builtins['header_directory'](header)
        self._builtins['install'](header)
        return header

    def _library(self, lib):
        if not isinstance(lib, DualUseLibrary):
            lib = self._builtins['library'](lib)
        self._builtins['install'](lib)
        return lib

    def _set_requires(self, value):
        reqs, system, deps = self._filter_packages(iterate(value))
        self._require_deps.extend(deps)
        return reqs, system

    def finalize(self):
        def _copy_reqs(requires):
            if requires:
                return requires[0].copy(), requires[1].copy()
            return RequirementSet(), []

        if self.name is None:
            raise ValueError('pkg-config package has no name')

        desc_name = self.desc_name or self.name
        includes = self.includes or []
        libs = self.libs or []
        libs_private = self.libs_private or []

        requires, extra = _copy_reqs(self.requires)
        requires_private, extra_private = _copy_reqs(self.requires_private)
        conflicts = self.conflicts or RequirementSet()

        require_build_deps = self._require_deps

        # Get all the build dependencies from source objects (includes, libs).
        # We expand these with `all` to account for DualUseLibraries.
        all_src = chain.from_iterable(i.all for i in chain(
            includes, libs, libs_private
        ))
        src_build_deps = [i for i in all_src if getattr(i, 'creator', None)]

        # Add all the (unique) dependent libs to libs_private, unless they're
        # already in libs.
        fwd = opts.ForwardOptions.recurse(chain(libs, libs_private))
        libs_private = uniques(chain(
            libs_private, (i for i in fwd.libs if i not in libs)
        ))

        # Get the package dependencies for all the libs (public and private)
        # that were passed in.
        auto_requires, auto_extra, auto_build_deps = self._filter_packages(
            chain.from_iterable(recursive_walk(
                i, 'package_deps', 'install_deps'
            ) for i in chain(libs, libs_private))
        )

        requires_private.update(auto_requires)
        requires.merge_from(requires_private)

        return {
            'name': self.name,
            'desc_name': desc_name,
            'desc': self.desc or '{} library'.format(desc_name),
            'lang': self.lang,
            'url': self.url,
            'version': self.version or '0.0',

            'includes': includes,
            'options': self.options,
            'libs': libs,
            'link_options': self.link_options,
            'libs_private': libs_private,
            'link_options_private': (fwd.link_options +
                                     self.link_options_private),

            'requires': requires.split(single=True),
            'requires_private': requires_private.split(single=True),
            'conflicts': conflicts.split(),

            'extra_pkgs': extra,
            'extra_pkgs_private': extra_private + auto_extra,
            'build_deps': (src_build_deps + require_build_deps +
                           auto_build_deps),
        }

    @staticmethod
    def _filter_packages(packages):
        pkg_config, system, deps = RequirementSet(), [], []
        for i in packages:
            if isinstance(i, str):
                pkg_config.add(Requirement(i))
                continue
            elif isinstance(i, (tuple, list)):
                pkg_config.add(Requirement(*i))
                continue
            elif isinstance(i, Package):
                if i.deps:
                    deps.append(i)

                if isinstance(i, (CommonPackage, GeneratedPkgConfigPackage)):
                    system.append(i)
                    continue
                elif isinstance(i, PkgConfigPackage):
                    pkg_config.add(Requirement(i.pcnames[0], i.specifier))
                    pkg_config.update(Requirement(i) for i in i.pcnames[1:])
                    continue

            raise TypeError('unsupported package type: {}'.format(type(i)))
        return pkg_config, uniques(system), deps


class PkgConfigWriter:
    directory = path.Path('pkgconfig')

    def __init__(self, context):
        self.context = context

    def _write_variable(self, out, name, value, syntax=Syntax.variable,
                        **kwargs):
        out.write(name, Syntax.variable)
        out.write_literal('=')
        out.write_each(iterate(value), syntax, **kwargs)
        out.write_literal('\n')

    def _write_field(self, out, name, value, syntax=Syntax.variable, **kwargs):
        if value:
            out.write(name, Syntax.variable)
            out.write_literal(': ')
            out.write_each(iterate(value), syntax, **kwargs)
            out.write_literal('\n')

    def _output_path(self, data, installed=True):
        basename = data['name'] + ('' if installed else '-uninstalled') + '.pc'
        return PkgConfigPcFile(self.directory.append(basename))

    def write(self, data, installed=True):
        path = self._output_path(data, installed)
        with make_immediate_file(self.context, path) as out:
            self._write(out, data, installed)
        return path

    def _installify(self, file):
        return self.context.build['install'].target[file]

    @staticmethod
    def _ensure_header_directory(file):
        if isinstance(file, HeaderFile):
            return HeaderDirectory(file.path.parent())
        return file

    def _write(self, out, data, installed):
        env = self.context.env
        installify_fn = self._installify if installed else identity

        # Get the compiler and linker to use for generating flags.
        builder = env.builder(data['lang'])
        compiler = builder.compiler
        linker = builder.linker('executable')

        compile_options = opts.option_list(
            (opts.include_dir(self._ensure_header_directory(installify_fn(i)))
             for i in data['includes']),
            data['options']
        )
        link_options = opts.option_list(
            (opts.lib(installify_fn(i.all[0])) for i in data['libs']),
            data['link_options']
        )
        link_options_private = opts.option_list(
            (opts.lib(installify_fn(i.all[0])) for i in data['libs_private']),
            data['link_options_private']
        )

        # Add the options from each of the system packages.
        for pkg in data['extra_pkgs']:
            compile_options.extend(pkg.compile_options(compiler, raw=True))
            link_options.extend(pkg.link_options(linker, raw=True))
        for pkg in data['extra_pkgs_private']:
            compile_options.extend(pkg.compile_options(compiler, raw=True))
            link_options_private.extend(pkg.link_options(linker, raw=True))

        cflags = compiler.flags(compile_options, mode='pkg-config')
        ldflags = (linker.flags(link_options, mode='pkg-config') +
                   linker.lib_flags(link_options, mode='pkg-config'))
        ldflags_private = (
            linker.flags(link_options_private, mode='pkg-config') +
            linker.lib_flags(link_options_private, mode='pkg-config')
        )

        # CMake expects POSIX-like paths in pkg-config files.
        out = Writer(out, localize_paths=False)

        if installed:
            for i in path.InstallRoot:
                if i != path.InstallRoot.bindir:
                    self._write_variable(out, i.name, env.install_dirs[i])
        else:
            self._write_variable(out, 'srcdir', env.srcdir)
            # Set the builddir to be relative to the .pc file's dir so that
            # users can move the build dir around and things still work.
            self._write_variable(out, 'builddir', path.Path('.').relpath(
                self.directory, prefix='${pcfiledir}', localize=False
            ))

        # We set absolute install_names when building mach-o libraries, but to
        # allow users to use the `-uninstalled` variant of the pkg-config file,
        # we need to let them know how to change the install_names in binaries
        # that use this package. Add an `install_names` variable that users can
        # compare between both variants that they can then pass to
        # `install_name_tool`.
        if builder.object_format == 'mach-o':
            all_libs = flatten(i.all for i in data['libs'])
            install_names = filter(None, (darwin_install_name(
                installify_fn(i), env, strict=False
            ) for i in all_libs))
            self._write_variable(out, 'install_names', install_names,
                                 Syntax.shell)

        out.write_literal('\n')

        name = data['desc_name']
        if not installed:
            name += ' (uninstalled)'

        self._write_field(out, 'Name', name)
        self._write_field(out, 'Description', data['desc'])
        self._write_field(out, 'URL', data['url'])
        self._write_field(out, 'Version', data['version'])
        self._write_field(out, 'Requires', data['requires'], Syntax.shell,
                          delim=literal(', '))
        self._write_field(out, 'Requires.private', data['requires_private'],
                          Syntax.shell, delim=literal(', '))
        self._write_field(out, 'Conflicts', data['conflicts'],
                          Syntax.shell, delim=literal(', '))
        self._write_field(out, 'Cflags', cflags, Syntax.shell)
        self._write_field(out, 'Libs', ldflags, Syntax.shell)
        self._write_field(out, 'Libs.private', ldflags_private, Syntax.shell)


def _write_pkg_config(context, info):
    data = info.finalize()
    writer = PkgConfigWriter(context)
    if can_install(context.env):
        installed_path = writer.write(data, installed=True)
        context['install'](installed_path)
    writer.write(data, installed=False)

    # XXX: Our usage of build_deps is a bit simplistic, since *everything* that
    # references this package will be considered dependent on it. This isn't
    # really accurate, since compilation steps don't generally care if the
    # package's libraries are fully-linked yet. However, given that this usage
    # of pkg-config files is already a corner case, it might not be worth the
    # added complexity to be smarter here.
    return context['alias']('pkg-config-' + data['name'], data['build_deps'])


@builtin.function()
def pkg_config(context, name=None, *, system=False, **kwargs):
    info = PkgConfigInfo(context, name, **kwargs)
    context.build['pkg_config'].append(info)

    if not info.auto_fill:
        dep_alias = _write_pkg_config(context, info)
        search_path = [PkgConfigWriter.directory.string(context.env.base_dirs)]
        try:
            return PkgConfigPackage(
                context.env.tool('pkg_config'), info.name,
                format=context.env.target_platform.object_format,
                system=system, deps=dep_alias, search_path=search_path
            )
        except FileNotFoundError:
            warnings.warn('unable to load local pkg-config package {!r}'
                          .format(info.name))
            return None


@builtin.post()
def finalize_pkg_config(context):
    build = context.build
    install = build['install']
    defaults = {
        'name': build['project'].name,
        'version': build['project'].version,

        # Get all the explicitly-installed headers/libraries.
        'includes': [i for i in install.explicit
                     if isinstance(i, (HeaderFile, HeaderDirectory))],
        'libs': [i for i in install.explicit
                 if isinstance(i, (Library, DualUseLibrary))],
    }

    for info in build['pkg_config']:
        if not info.auto_fill:
            continue
        for key, value in defaults.items():
            if getattr(info, key) is None:
                setattr(info, key, value)

    # Make sure we don't have any duplicate pkg-config packages.
    dupes = Counter(i.name for i in build['pkg_config'])
    for name, count in dupes.items():
        if count > 1:
            raise ValueError("duplicate pkg-config package '{}'".format(name))

    for info in build['pkg_config']:
        if info.auto_fill:
            _write_pkg_config(context, info)
