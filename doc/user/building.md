# Building With bfg9000

Like some other tools (e.g. [CMake][cmake] or [autotools][autotools]), bfg9000
isn't actually a build system; it's a *build configuration system* or, if you
prefer, a *meta-build system*. That is, bfg9000 builds build files which you
then use to run your actual builds.

## Your first build

Invoking bfg9000 is simple. Assuming you have an existing project that uses
bfg9000, just call `bfg9000 configure builddir` and it will generate the final
build script (`build.ninja` in this case) in `builddir` to use for
building your project:

```sh
$ cd /path/to/src/
$ bfg9000 configure builddir/
$ cd builddir/
$ ninja
```

Since the configure command is easily the most common thing to run when using
bfg9000, you can use the following shorthand instead of
`bfg9000 configure builddir/`:

```sh
$ 9k builddir/
```

!!! note
    On Windows, using bfg9000 requires a bit more care. Since the MSVC tools
    aren't in the `PATH` by default, you can't just open any command prompt.
    You need to pick the *correct* prompt. Thankfully, Visual Studio provides
    Start Menu items such as "VS2015 Developer Command Prompt". These add the
    appropiate directories to the `PATH`, allowing you to use whichever version
    of the MSVC tools that you'd like.

## Build directories

You might have noticed above that `build.ninja` was placed in a separate
directory. This is because bfg9000 exclusively uses *out-of-tree builds*; that
is, the build directory must be different from the source directory. While
slightly more inconvenient for one-off builds (users will have to `cd` into
another directory to start the build), the benefits are significant. First, it
ensures that cleaning a build is trivial: just remove the build directory.
Second, simplifies building in multiple configurations, a very useful feature
for development; you can easily have debug and optimized builds sitting
side-by-side.

In our example above, we specified the build directory to place the final build
files. However, you can also run bfg9000 *from* the build directory, in which
case you'd run `bfg9000 configure srcdir/` (or, equivalently, `9k srcdir/`). If
neither the source nor build directories are your current working directory, you
can run:

```sh
$ bfg9000 configure-into srcdir/ builddir/
```

## Selecting a backend

By default, bfg9000 tries to use the most appropriate build backend for your
system. In descending order, bfg prefers [`ninja`][ninja], [`make`][make], and
[`msbuild`][msbuild]. If one of these isn't installed, it will try the next best
option. However, you can explicitly select a backend with the `--backend`
option. For instance, to build a Makefile even if Ninja is installed:

```sh
$ bfg9000 configure builddir/ --backend=make
```

For a complete description of the available command-line options for bfg9000,
see the [Command-line Reference](../reference/command-line.md) chapter.

## Setting build options

Many options for building can be set via the environment. These generally follow
the UNIX naming conventions, so you can use, say,
[`CXX`](../reference/environment-vars.md#cxx) to change the C++ compiler that
bfg9000 uses. For a full listing of the recognized environment variables, see
the [Environment Variables](../reference/environment-vars.md) chapter.

## Using toolchain files

In order to simplify setting up all the myriad options required for certain
builds (and to share those settings with others), bfg9000 allows users to use
toolchain files that define all this. To use an existing toolchain file, just
use the `--toolchain` option during configuration:

```sh
$ bfg9000 configure builddir/ --toolchain my_toolchain.bfg
```

### Writing a toolchain file

Toolchain files, like other `.bfg` files, are just Python scripts with some
extra built-in functions. However, *unlike* other `.bfg` files, toolchain files
have a few restrictions: file access and `import` statements are disabled. Since
many users will copy toolchain files from other sources to build for a specific
target, this helps reduce the potential for unwanted things from happening while
building your software.

Generally, toolchain files will set up relevant compilers, compilation options,
and other aspects of the environment. These settings are then forwarded on to
the `build.bfg` script proper. Below is a simple toolchain file that
demonstrates some common settings:

```python
target_platform('windows', 'x86_64')

compiler('x86_64-w64-mingw32-g++-win32', 'c++')
compile_options(['-Wall'], 'c++')
```

For more information on the available builtins, see the [reference
guide](../reference/builtins.md#toolchain).

## Installing your software

After building your software, you may wish to install it to another directory on
your system. You can do this by running:

```sh
$ ninja install
```

Similarly, you can run `ninja uninstall` to uninstall the files from their
install location. Of course, if you're using the Make backend, you'd run
`make install`/`make uninstall` instead.

!!! warning
    The MSBuild backend doesn't currently support this command.

### Install locations

By default, bfg9000 will install them into the appropriate place for your
platform (e.g. `/usr/local/bin` for exectuables on POSIX systems).  However, you
can specify where you'd like to install your project when invoking bfg9000. To
change the installation prefix (`/usr/local` on POSIX), just specify `--prefix
/path/to/prefix` when running bfg9000. You can also specify the binary, library,
and include directories individually, using `--bindir`, `--libdir`, and
`--includedir`, respectively.

!!! note
    On POSIX systems, you can additionally specify the $DESTDIR environment
    variable to perform a staged installation (useful when creating a binary
    package, for example). For more information about $DESTDIR, see the [GNU
    coding standards][destdir].

## Distributing your source

Once you're ready to release your software, you'll want to provide a source
distribution. You can't just archive the entire source directory, since it'll
include things that don't belong like `.gitignore`. Instead, you should run:

```sh
$ ninja dist
```

(Of course, you should run `make dist` for the Make backend.) This will produce
a `tar.gz` file containing all the source files necessary for building your
project. If you'd like to specify another file format, you can use one of the
following targets: `dist-gzip`, `dist-bzip2`, or `dist-zip`.

!!! warning
    The MSBuild backend doesn't currently support this command.

[cmake]: https://www.cmake.org/
[autotools]: https://www.gnu.org/software/automake/
[ninja]: https://ninja-build.org/
[make]: https://www.gnu.org/software/make/
[msbuild]: https://msdn.microsoft.com/en-us/library/dd393574(v=vs.120).aspx
[destdir]: https://www.gnu.org/prep/standards/html_node/DESTDIR.html
