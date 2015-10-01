# Building With bfg9000

Like some other tools (e.g. [CMake](http://www.cmake.org/) or
[autotools](https://www.gnu.org/software/automake/)), bfg9000 isn't actually a
build system; it's a *build configuration system* or, if you prefer, a
*meta-build system*. That is, bfg9000 builds build files which you then use to
run your actual builds.

## Your first build

Invoking bfg9000 is simple. Assuming you have an existing project that uses
bfg9000, just call `bfg9000 srcdir builddir` and it will generate the final
build script (`build.ninja` in this case) in `builddir` to use for
building your project:

```sh
$ bfg9000 path/to/src/ build/
$ cd build
$ ninja
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

## Setting options

Many options for building can be set via the environment. These generally follow
the UNIX naming conventions, so you can use `CFLAGS`, `CXXFLAGS`, and `CPPFLAGS`
for compilation flags, `LDFLAGS` for linker flags, and `LIBRARY_PATH` for the
list of library search directories.
