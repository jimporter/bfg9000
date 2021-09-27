import warnings

from . import builtin
from .. import options as opts
from ..exceptions import PackageResolutionError
from ..file_types import Executable
from ..iterutils import default_sentinel, listify
from ..objutils import objectify
from ..packages import CommonPackage, Framework, Package, PackageKind
from ..path import Path, Root
from ..shell import which
from ..versioning import InvalidSpecifier, SpecifierSet


@builtin.function()
@builtin.type(Package)
def package(context, name, submodules=None, version=default_sentinel, *,
            lang=None, kind=PackageKind.any.name, headers=default_sentinel,
            libs=default_sentinel, system=True):
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
    return resolver.resolve(name, listify(submodules), version, kind,
                            headers=headers or None, libs=libs or None,
                            system=system)


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
