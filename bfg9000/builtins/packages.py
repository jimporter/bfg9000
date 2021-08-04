import re
import warnings

from . import builtin
from .. import options as opts
from ..exceptions import PackageResolutionError, PackageVersionError
from ..file_types import Executable
from ..iterutils import default_sentinel, listify
from ..objutils import objectify
from ..packages import CommonPackage, Framework, Package, PackageKind
from ..path import Path, Root
from ..shell import which
from ..versioning import check_version, InvalidSpecifier, SpecifierSet, Version


# XXX: This is a bit of a hack. It would probably be better to put this in
# mopack instead. However, this would require mopack to be able to do all the
# work of finding header files.
def _boost_version(include_dirs, required_version):
    for path in include_dirs:
        version_hpp = path.append('boost').append('version.hpp')
        try:
            with open(version_hpp.string()) as f:
                for line in f:
                    m = re.match(
                        r'#\s*define\s+BOOST_LIB_VERSION\s+"([\d_]+)"', line
                    )
                    if m:
                        version = Version(m.group(1).replace('_', '.'))
                        check_version(version, required_version, 'boost',
                                      PackageVersionError)
                        return version
        except FileNotFoundError:
            pass
    raise PackageVersionError('unable to parse "boost/version.hpp"')


@builtin.function()
@builtin.type(Package)
def package(context, name, submodules=None, version=default_sentinel, *,
            lang=None, kind=PackageKind.any.name, headers=default_sentinel,
            libs=default_sentinel):
    if version is default_sentinel:
        version = SpecifierSet()
        if submodules and isinstance(submodules, (str, SpecifierSet)):
            try:
                version = objectify(submodules, SpecifierSet)
                submodules = None
            except InvalidSpecifier:
                pass
    else:
        version = objectify(version or '', SpecifierSet)

    kind = PackageKind[kind]

    if ( headers is not default_sentinel or
         libs is not default_sentinel ):  # pragma: no cover
        # TODO: Remove this after 0.7 is released.
        warnings.warn('"headers" and "libs" are deprecated; use mopack.yml ' +
                      'file instead')

    if lang is None:
        lang = context.build['project']['lang']

    resolver = context.env.builder(lang).packages
    get_version = _boost_version if name == 'boost' else None
    return resolver.resolve(name, listify(submodules), version, kind,
                            get_version=get_version, headers=headers or None,
                            libs=libs or None)


@builtin.function()
@builtin.type(Executable)
def system_executable(context, name, format=None):
    env = context.env
    return Executable(
        Path(which([[name]], env.variables, resolve=True)[0], Root.absolute),
        format or env.host_platform.object_format
    )


@builtin.function()
def framework(context, name, suffix=None):
    env = context.env
    if not env.target_platform.has_frameworks:
        raise PackageResolutionError("{} platform doesn't support frameworks"
                                     .format(env.target_platform.name))

    framework = Framework(name, suffix)
    return CommonPackage(framework.full_name,
                         format=env.target_platform.object_format,
                         link_options=opts.option_list(opts.lib(framework)))


@builtin.function()
def boost_package(context, name=None, version=None):
    # TODO: Remove this after 0.7 is released.
    warnings.warn('"boost_package(...) is deprecated; use ' +
                  '"package(\'boost\', ...) instead')
    return package(context, 'boost', name, version)
