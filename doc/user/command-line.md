# Command-Line Reference

## Global options

#### -h, --help { #help-option }

Print a help message and exit. Equivalent to the [`help`](#help) subcommand.

#### --version { #version }

Print the version number and exit.

#### -c, --color *WHEN* { #color }

Show colored output; *WHEN* is one of `always`, `never`, or `auto` and defaults
to `auto` (i.e. show colored output when the terminal is a tty). `-c` is
equivalent to `--color=always`.

#### --warn-once { #warn-once }

Only emit a given warning once.

## Sub-commands

### bfg9000 help [*SUBCOMMAND*] { #help }

Print a help message and exit. If *SUBCOMMAND* is specified, print help for that
subcommand.

### bfg9000 configure *DIRECTORY* { #configure }

Generate the necessary build files to perform actual builds. If *DIRECTORY* is a
source directory (i.e. it contains a build.bfg file), the build files will be
created in the current directory. Otherwise, *DIRECTORY* is treated as the build
directory, and bfg9000 will look for a build.bfg file in the current directory.

#### --backend *BACKEND* { #configure-backend }

The kind of build files to generate; one of `ninja`, `make`, or `msbuild`. The
default value depends on what build backends you have installed, but if `ninja`
is present on your system, it will be the default.

#### --enable-shared, --disable-shared { #configure-enable-shared }

Enable/disable building shared libraries when using
[*library*()](reference.md#library) in your build.bfg files. Defaults to enabled.

#### --enable-static, --disable-static { #configure-enable-static }

Enable/disable building static libraries when using
[*library*()](reference.md#library) in your build.bfg files. Defaults to enabled.

#### --prefix *PATH* { #configure-prefix }

The installation prefix to use when installing built files. On Linux and macOS,
this defaults to `/usr/local`; on Windows, there is no default (thus, to
install built files on Windows, you must either set `--prefix` or one of the
other install path options below).

#### --exec-prefix *PATH* { #configure-exec-prefix }

The installation prefix to use when installing architecture-dependent files
(e.g. executables). This defaults to the value of
[`--prefix`](#configure-prefix).

#### --bindir *PATH* { #configure-bindir }

The installation prefix to use for executables. Defaults to `<prefix>/bin` on
Linux and macOS, and `<prefix>` on Windows.

#### --libdir *PATH* { #configure-libdir }

The installation prefix to use for libraries. Defaults to `<prefix>/lib` on
Linux and macOS, and `<prefix>` on Windows.

#### --includedir *PATH* { #configure-includedir }

The installation prefix to use for headers. Defaults to `<prefix>/include` on
Linux and macOS, and `<prefix>` on Windows.

### bfg9000 configure-into *SRCDIR* *BUILDDIR* { #configure-into }

Generate the necessary build files (as with [`bfg9000 configure`](#configure))
to perform actual builds from a build.bfg file in *SRCDIR*, and place them in
*BUILDDIR*.

### bfg9000 refresh [*BUILDDIR*] { #refresh }

Regenerate an existing set of build files in *BUILDDIR* needed to perform actual
builds. This is run automatically if bfg9000 determines that the build files are
out of date.

### bfg9000 env [*BUILDDIR*] { #env }

Print the environment variables stored by the build configuration in *BUILDDIR*.

#### -u, --unique { #env-unique }

Only show environment variables that differ from the current environment.

## 9k shorthand

`9k` is a special shorthand to make it easier to configure your build. It's
equivalent to [`bfg9000 configure`](#configure).
