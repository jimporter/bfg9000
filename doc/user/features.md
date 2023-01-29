# Features

## Supported languages/platforms

bfg9000 is designed to work on Linux, OS X, and Windows; other POSIX systems
should work as well, but they aren't explicitly supported (if you'd like to help
add support for your favorite platform, just file a pull request!). In addition,
bfg9000 supports building code written in the following languages:

* C
* C++
* Fortran
* Java
* Objective C/C++
* Scala
* ... [and more](../reference/languages.md)

Finally, bfg supports generating build files for [Make][make], [Ninja][ninja],
and [MSBuild][msbuild], defaulting to Ninja.

## Rich scripting

Since `build.bfg` (and `options.bfg`!) files are just Python scripts with some
extra builtins, it's possible to use the entirety of the Python ecosystem in
your build scripts. This allows you to perform complex operations in your build
scripts without having to roll everything yourself or provide a layer of "glue"
to some external scripts in your build process.

## Flexible package dependencies

bfg9000 integrates with [`mopack`][mopack] to provide support for getting
external package dependencies from multiple sources and allowing people building
your project to easily override how packages are found. It's also easy to
[generate](../reference/builtins.md#pkg_config) [`pkg-config`][pkg-config] `.pc`
files for your own packages to simplify using them elsewhere.

## Project-defined arguments

Projects can specify their own options, complete with help instructions, in the
[`options.bfg`](writing.md#options), making it easy to help users get your
project configured for their system.

## Semantic options

To simplify building your software with different compilers, many common
compiler flags can be represented with [semantic
options](../reference/builtins.md#semantic-options). These will then be
translated to the appropriate syntax for the selected compiler.

## Toolchains for cross-compilation

When configuring a build, you can take advantage of [toolchain
files](building.md#using-toolchain-files), which specify the necessary settings
(e.g. environment variables) for properly building your software, especially
useful for cross-compilation configurations.

## Intelligent rpath support

bfg9000 automatically specifies rpaths on platforms that support them
(currently Linux and macOS), making it easier to produce correct builds. When
building, bfg always produces relative rpaths to allow moving your build
directory without breaking things; however, when installing your build, these
rpaths are modified to absolute paths (using [`patchelf`][patchelf] on Linux and
[`install_name_tool`][install_name_tool] on macOS).

## Auto-sudo during installation

When installing your builds, the install tool ([`doppel`][doppel]) will
automatically request sudo priveleges if the installation directory requires it.
This allows you to run `ninja install` as a non-root user, preventing
permissions issues with intermediate files as well as being more secure.

## pkg-config lookup and generation

bfg9000 supports [`pkg-config`][pkg-config] both for looking up packages as well
as [generating](../reference/builtins.md#pkg_config) `.pc` files for your own
packages.

[ninja]: https://ninja-build.org/
[make]: https://www.gnu.org/software/make/
[msbuild]: https://learn.microsoft.com/en-us/visualstudio/msbuild/msbuild
[mopack]: https://jimporter.github.io/mopack/
[pkg-config]: https://www.freedesktop.org/wiki/Software/pkg-config/
[patchelf]: https://nixos.org/patchelf.html
[install_name_tool]: https://www.unix.com/man-page/osx/1/install_name_tool/
[doppel]: https://github.com/jimporter/doppel/
