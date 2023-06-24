# Command-Line Reference

## Global options

#### `-h`, `--help` { #help-option }

Print a help message and exit. Equivalent to the [`help`](#help) subcommand.

#### `--version` { #version }

Print the version number and exit.

#### `-c`, <code>--color *WHEN*</code> { #color }

Show colored output; *WHEN* is one of `always`, `never`, or `auto` and defaults
to `auto` (i.e. show colored output when the terminal is a tty). `-c` is
equivalent to `--color=always`.

#### `--warn-once` { #warn-once }

Only emit a given warning once.

## Sub-commands

### <code>bfg9000 help [*SUBCOMMAND*]</code> { #help }

Print a help message and exit. If *SUBCOMMAND* is specified, print help for that
subcommand.

### <code>bfg9000 configure *DIRECTORY*</code> { #configure }

Generate the necessary build files to perform actual builds. If *DIRECTORY* is a
source directory (i.e. it contains a build.bfg file), the build files will be
created in the current directory. Otherwise, *DIRECTORY* is treated as the build
directory, and bfg9000 will look for a build.bfg file in the current directory.

#### <code>-B *BACKEND*</code>, <code>--backend *BACKEND*</code> { #configure-backend }

The kind of build files to generate; one of `ninja`, `make`, or `msbuild`. The
default value depends on what build backends you have installed, but if `ninja`
is present on your system, it will be the default.

#### <code>--toolchain *FILE*</code> { #configure-toolchain }

An optional [toolchain file](../user/building.md#using-toolchain-files) that
can be used to easily set all the options required for a certain build.

#### `--enable-shared`, `--disable-shared` { #configure-enable-shared }

Enable/disable building shared libraries when using
[*library*()](builtins.md#library) in your build.bfg files. Defaults to enabled.

#### `--enable-static`, `--disable-static` { #configure-enable-static }

Enable/disable building static libraries when using
[*library*()](builtins.md#library) in your build.bfg files. Defaults to enabled.

#### `--enable-compdb`, `--disable-compdb` { #configure-enable-compdb }

Enable/disable generation of `compile_commands.json` when generating build
files. Defaults to enabled.

#### <code>-p *FILE*</code>, <code>--package-file *FILE*</code> { #configure-package-file }

Additional [mopack][mopack] package files to consult when resolving packages.

#### <code>-P *FLAG*</code>, <code>--package-flag *FLAG*</code> { #configure-package-flag }

Additional [mopack][mopack] flags to use when resolving packages.

#### `--no-resolve-packages` { #configure-no-resolve-packages }

Disable resolution of package dependencies via [mopack][mopack].

#### <code>--prefix *PATH*</code> { #configure-prefix }

The installation prefix to use when installing built files. On Linux and macOS,
this defaults to `/usr/local`; on Windows, there is no default (thus, to
install built files on Windows, you must either set `--prefix` or one of the
other install path options below).

#### <code>--exec-prefix *PATH*</code> { #configure-exec-prefix }

The installation prefix to use when installing architecture-dependent files
(e.g. executables). This defaults to the value of
[`--prefix`](#configure-prefix).

#### <code>--bindir *PATH*</code> { #configure-bindir }

The installation prefix to use for executables. Defaults to `<exec-prefix>/bin`
on Linux and macOS, and `<exec-prefix>` on Windows.

#### <code>--libdir *PATH*</code> { #configure-libdir }

The installation prefix to use for libraries. Defaults to `<exec-prefix>/lib` on
Linux and macOS, and `<exec-prefix>` on Windows.

#### <code>--includedir *PATH*</code> { #configure-includedir }

The installation prefix to use for headers. Defaults to `<prefix>/include` on
Linux and macOS, and `<prefix>` on Windows.

#### <code>--datadir *PATH*</code> { #configure-includedir }

The installation prefix to use for data files. Defaults to `<prefix>/share` on
Linux and macOS, and `<prefix>` on Windows.

#### <code>--mandir *PATH*</code> { #configure-mandir }

The installation prefix to use for man pages. Defaults to `<datadir>/man`.

### <code>bfg9000 configure-into *SRCDIR* *BUILDDIR*</code> { #configure-into }

Generate the necessary build files (as with [`bfg9000 configure`](#configure))
to perform actual builds from a build.bfg file in *SRCDIR*, and place them in
*BUILDDIR*.

### <code>bfg9000 regenerate [*BUILDDIR*]</code> { #regenerate }

Regenerate an existing set of build files in *BUILDDIR* needed to perform actual
builds. This is run automatically if bfg9000 determines that the build files are
out of date.

### <code>bfg9000 env [*BUILDDIR*]</code> { #env }

Print the environment variables stored by the build configuration in *BUILDDIR*.

#### `-u`, `--unique` { #env-unique }

Only show environment variables that differ from the current environment.

### <code>bfg9000 run *COMMAND*</code> { #run }

Run an arbitrary *COMMAND* with the environment variables set for the current
build.

#### `-I`, `--initial` { #run-initial }

Use the *initial* environment variables, before any modification by toolchain
files.

#### <code>-B *BUILDDIR*</code>, <code>--builddir *BUILDDIR*</code> { #run-builddir }

Set the build directory to pull environment variable state from.

### `bfg9000 generate-completion` { #generate-completion }

Generate shell-completion functions for bfg9000 and write them to standard
output. This requires the Python package [shtab][shtab].

#### <code>-p *PROGRAM*</code>, <code>--program *PROGRAM*</code> { #generate-completion-program }

Specify the program to generate completion for: `bfg9000` (the default) or `9k`.

#### <code>-s *SHELL*</code>, <code>--shell *SHELL*</code> { #generate-completion-shell }

Specify the shell to generate completion for, e.g. `bash`. Defaults to the
current shell's name.

## `9k` shorthand

`9k` is a special shorthand to make it easier to configure your build. It's
equivalent to [`bfg9000 configure`](#configure).

[mopack]: https://jimporter.github.io/mopack/
[shtab]: https://github.com/iterative/shtab
