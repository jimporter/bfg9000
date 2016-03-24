# Reference

## File types

### directory(*name*)

Create a reference to an existing directory named *name*. This allows you to
refer to an arbitrary subfolder of your source directory.

### header(*name*)

Create a reference to an existing header named *name*. This is useful if you'd
like to [install](#install) a single header file for your project.

### header_directory(*name*, [*system*])

Create a reference to a directory named *name* containing header files for the
project. This can then be used in the *include* argument when
[compiling](#object_filename-file-extra_deps) a source file. If *system* is
*True*, this directory will be treated as a
[system directory](https://gcc.gnu.org/onlinedocs/cpp/System-Headers.html) for
compilers that support this.

### source_file(*name*, [*lang*])

Create a reference to an existing source file named *name*. If *lang* is not
specified, the language of the file is inferred from its extension. Generally,
this function is only necessary when running commands that take a source file
as an argument, e.g. running a Python script; this allows you to specify that
the file is found in the *source directory*. In other cases, a plain string will
automatically get converted to a *source_file*.

## Build steps

Build steps define rules to create an output (usually a file) from zero or more
inputs (also usually files). As you may expect, if the output doesn't exist, the
step is run to generate it. Each input is a dependency on the output, and any
changes to an input will result in a rebuild. This includes headers `#include`d
by any of the source files, but does *not* include files external to the project
(i.e. [packages](#package-resolvers)).

In addition, all build steps have the ability to define extra dependencies via
the *extra_deps* argument. These can be files or other build steps, and changes
to them will trigger a rebuild as with the build's inputs.

!!! note
    For build steps which produce an actual file, the exact name of the output
    file is determined by the platform you're running on. For instance, when
    building an executable file named "foo" on Windows, the resulting file will
    be `foo.exe`.

### command(*name*, *cmd*|*cmds*, [*environment*], [*extra_deps*])

Create a build step that runs a list of arbitrary commands, specified in either
*cmd* or *cmds*; *cmd* takes a single command, whereas *cmds* takes a list of
commands. Each command may either be a string to be parsed according to shell
rules or a list of arguments to be passed directly to the process.

You may also pass a dict to *environment* to set environment variables for the
commands. These override any environment variables set on the command line.

### executable(*name*, [*files*, ..., [*extra_deps*]])

Create a build step that builds an executable file named *name*. *files* is the
list of source (or object) files to link. If an element of *files* is a source
file (or a plain string), this function will implicitly call
[*object_file*](#object_filename-file-extra_deps) on it.

The following arguments may also be specified:

* *include*: Forwarded on to [*object_file*](#object_filename-file-extra_deps)
* *libs*: A list of library files (see *shared_library* and *static_library*)
* *packages*: A list of external [packages](#package-finders); also forwarded on
  to *object_file*
* *compile_options*: Forwarded on to
  [*object_file*](#object_filename-file-extra_deps) as *options*
* *link_options*: Command-line options to pass to the linker
* *lang*: Forwarded on to [*object_file*](#object_filename-file-extra_deps)

If *files* isn't specified, this function merely references an *existing*
executable file (a precompiled binary, a shell script, etc) somewhere on the
filesystem. In this case, *name* is the exact name of the file, relative to the
source directory. This allows you to refer to existing executables for other
functions. In addition, the following arguments may be specified:

* *format*: The object format of the exectuable; by default, this is the
  platform's native object format (e.g. `'elf'` on Linux)

This build step recognizes the [dynamic linking environment
variables](environment-vars.md#dynamic-linking) and the [compiler environment
variable](environment-vars.md#compilation-variables) (e.g. `CC`) for the
relevant language.

### object_file([*name*], [*file*, ..., [*extra_deps*]])

Create a build step that compiles a source file named *file* to an object file
named *name*; if *name* is not specified, it takes the file name in *file*
without the extension.

The following arguments may also be specified:

* *include*: A list of [directories](#header_directorydirectory) to search for
  header files
* *packages*: A list of external [packages](#package-finders)
* *options*: Command-line options to pass to the compiler
* *lang*: The language of the source file; useful if the source file's extension
  isn't recognized by bfg9000

If *file* isn't specified, this function merely references an *existing*
object file somewhere on the filesystem. In this case, *name* must be specified
and is the exact name of the file, relative to the source directory. In
addition, the following arguments may be specified:

* *format*: The object format of the file; by default, this is the platform's
  native object format (e.g. `'elf'` on Linux)
* *lang*: The source language of the file; if none is specified, defaults to
  `'c'`

This build step recognizes the [compilation environment
variables](environment-vars.md#compilation-variables) for the relevant language.

### object_files(*files*, ..., [*extra_deps*])

Create a compilation build step for each of the files in *files*; this is
equivalent to calling [*object_file*](#object_filename-file-extra_deps) for each
element in *files*.

In addition, *object_files* returns a special list that allows you to index into
it using the filename of one of the source files listed in *files*. This makes
it easy to extract a single object file to use in other places, e.g. test code.
For example:

```python
objs = object_files(['foo.cpp', 'bar.cpp'])
release_exe = executable('release', objs)

foo_obj = objs['foo.cpp']
test_exe = executable('test', ['test.cpp', foo_obj])
```

### shared_library(*name*, [*files*, ..., [*extra_deps*]])

Create a build step that builds a shared library named *name*. Its arguments are
the same as [*executable*](#executablename-files-extra_deps), with the following
additional options:

* *version*: The version number of the library, e.g. `1.2.3`.
* *soversion*: The API version of the library (used in its soname), e.g. `1`.

Like with *executable*, if *files* isn't specified, this function merely
references an *existing* shared library somewhere on the filesystem. In this
case, *name* must be specified and is the exact name of the file, relative to
the source directory. You may also pass in the *format* argument as with
*executable*.

This build step recognizes the [dynamic linking environment
variables](environment-vars.md#dynamic-linking) and the [compiler environment
variable](environment-vars.md#compilation-variables) (e.g. `CC`) for the
relevant language.

!!! note
    On Windows, this produces *two* files for native-runtime languages (e.g. C
    or C++): `name.dll` and `name.lib`. The latter is the *import library*, used
    when linking to this library. As a result, `my_lib.all` returns a list
    containing *two* files.

    Additionally for native languages on Windows, this step will add a
    preprocessor macro named `LIB<NAME>_EXPORTS` that can be used for declaring
    public symbols. See [Building libraries on
    Windows](writing.md#building-libraries-on-windows) for an example of how to
    use this macro in your code.

### static_library(*name*, [*files*, ..., [*extra_deps*]])

Create a build step that builds a static library named *name*. Its arguments are
the same as [*executable*](#executablename-files-extra_deps). Link-related
arguments (*link_options*, *libs*, and libraries from *packages*) have no direct
effect on this build step. Instead, they're cached and forwarded on to any
dynamic linking step that uses this static library.

Like with *executable*, if *files* isn't specified, this function merely
references an *existing* shared library somewhere on the filesystem. In this
case, *name* must be specified and is the exact name of the file, relative to
the source directory. In addition, the following arguments may be specified:

* *format*: The object format of the exectuable; by default, this is the
  platform's native object format (e.g. `'elf'` on Linux)
* *lang*: The source language(s) of the library; if none is specified, defaults
  to `['c']`

This build step recognizes the [static linking environment
variables](environment-vars.md#static-linking).

!!! note
    On Windows, this step will add a preprocessor macro on Windows named
    `LIB<NAME>_STATIC` that can be used for declaring public symbols. See
    [Building libraries on Windows](writing.md#building-libraries-on-windows)
    for an example of how to use this macro in your code.

### whole_archive(*name*, [*files*, ..., [*extra_deps*]])

Create a build step that builds a [whole-archive](http://linux.die.net/man/1/ld)
named *name*. Whole archives ensures that *every* object file in the library is
included, rather than just the ones whose symbols are referenced. This is
typically used to turn a static library into a shared library.

*whole_archive*'s arguments are the same as for
[*static_library*](#static_libraryname-files-extra_deps). In addition, you can
pass an existing static library to *whole_archive* to convert it into a whole
archive.

!!! warning
    The MSVC linker doesn't have a way of expressing the required directives, so
    *whole_archive* can't be used with it.

## Grouping rules

### alias(*name*, [*deps*])

Create a build step named *name* that performs no actions on its own. Instead,
it just runs its dependencies listed in *deps* as necessary. This build step is
useful for grouping common steps together.

### default(*...*)

Specify a list of build steps that should be run by default when building. These
are all accumulated into the `all` target. If *default* is never called, all
executables and libraries *not* passed to
[*test*](#testtest-options-environmentdriver) will be built by default.

### install(*...*)

Specify a list of files that need to be installed for the project to work. Each
will be installed to the appropriate location based on its type, e.g. header
files will go in `$PREFIX/include` by default on POSIX systems. These are all
accumulated into the `install` target. If there are any runtime dependencies for
a file (such as shared libraries you just built), they will be installed as
well.

!!! note
    When explicitly listing a target, *all* the files for that target will be
    installed. For instance, on Windows, this means that passing in a shared
    library will install the DLL *and* the import library.

This rule recognizes the following environment variables:
[`INSTALL`](environment-vars.md#install),
[`INSTALL_NAME_TOOL`](environment-vars.md#install_name_tool),
[`MKDIR_P`](environment-vars.md#mkdir_p),
[`PATCHELF`](environment-vars.md#patchelf).

## Global options

### global_options(*options*, *lang*)

Specify some *options* (either as a string or list) to use for all compilation
steps for the language *lang*.

### global_link_options(*options*)

Specify some *options* (either as a string or list) to use for all link steps
(i.e. for [executables](#executablename-files-extra_deps) and
[shared libraries](#shared_libraryname-files-extra_deps)).

## Test rules

These rules help you define automated tests that can all be run via the `test`
target. For simple cases, you should only need the
[*test*](#testtest-options-environmentdriver) rule, but you can also wrap your
tests with a separate driver using
[*test_driver*](#test_driverdriver-options-environmentparent).

For cases where you only want to *build* the tests, not run them, you can use
the `tests` target.

### test(*test*, [*options*], [*environment*|*driver*])

Create a test for a single test file named *test*. You may specify additional
command-line arguments to the test in *options*. You can also pass temporary
environment variables as a dict via *environment*, or specify a test driver to
add this test file to via *driver*.

### test_driver(*driver*, [*options*], [*environment*|*parent*])

Create a test driver which can run a series of tests, specified as command-line
arguments to the driver. You may specify driver-wide command-line arguments via
*options*. You can also pass temporary environment variables as a dict with
*environment*, or specify a parent test driver to wrap this driver via *driver*.

### test_deps(*...*)

Specify a list of dependencies which must be satisfied before the tests can be
run.

## Package resolvers

### boost_package([*name*], [*version*])

Search for a [Boost](https://www.boost.org/) library. You can specify *name* (as
a string or a list) to specify a specific Boost library (or libraries); for
instance, `'program_options'`. For header-only libraries, you can omit *name*.
If *version* is specified, it will ensure that the installed version of Boost
meets the version requirement; it must be formatted as a Python [version
specifier](https://www.python.org/dev/peps/pep-0440/#version-specifiers).

This rule recognizes the [packaging environment
variables](environment-vars.md#packaging-variables).

### pkgconfig_package(*name*, [*version*], [*lang*])

Search for a package named *name* via
[pkg-config](https://www.freedesktop.org/wiki/Software/pkg-config/). If
*version* is specified, it will ensure that the installed version of the package
meets the version requirement; it must be formatted as a Python [version
specifier](https://www.python.org/dev/peps/pep-0440/#version-specifiers). *lang*
is the source language of the library (`'c'` by default); this is useful if you
need to link a static library written in C++ with a program written in C.

This rule recognizes the following environment variable:
[`PKG_CONFIG`](environment-vars.md#pkg_config),

### system_executable(*name*)

Search for an executable named *name* somewhere in the system's PATH.

This rule recognizes the following environment variables:
[`PATH`](environment-vars.md#path), [`PATHEXT`](environment-vars.md#pathext).

### system_package(*name*, [*lang*], [*kind*])

Search for a library named *name* somewhere in the system's default library
location. *lang* is the source language of the library (`'c'` by default); this
is useful if you need to link a static library written in C++ with a program
written in C.

You can also specify *kind* to one of `'any'` (the default), `'shared'`, or
`'static'`. This allows you to restrict the search to find only static versions
of a library, for example.

This rule recognizes the following environment variables:
[`LIB`](environment-vars.md#lib),
[`LIBRARY_PATH`](environment-vars.md#library_path).

!!! note
    This only finds the library itself, not any required headers. Those are
    assumed to be somewhere where your compiler can find them automatically; if
    not, you can set [`CPPFLAGS`](environment-vars.md#cppflags) to add the
    appropriate header search path.

## Environment

The *environment*, `env`, is a special object that encapsulates information
about the system outside of bfg9000. It's used internally for nearly all
platform-specific code, but it can also help in `build.bfg` files when you
encounter some unavoidable issue with multiplatform compatibility.

!!! note
    This listing doesn't cover *all* available functions on the environment,
    since many are only useful to internal code. However, the most relevant ones
    for `build.bfg` files are shown below.

### env.builder(*lang*)

Return the builder used by bfg9000 for a particular language *lang*. While
builder objects are primarily suited to bfg's internals, there are still a few
useful properties for `build.bfg` files:

#### builder.flavor

The "flavor" of the builder, i.e. the kind of command-line interface it has.
Possible values are `'cc'` and `'msvc'`.

#### builder.flavor

The brand of the builder, i.e. the commonad name people use for it. Possible
values are `'gcc'`, `'clang'`, `'msvc'`, and `'unknown'`.

#### builder.compiler

The compiler used with this builder.

##### compiler.command

The command to run when invoking this compiler, e.g. `g++-4.9`.

### builder.linker(*mode*)

The linker used with this builder. *mode* is one of `'executable'`,
`'shared_library'`, or `'static_library'`. Its public properties are the same as
[*compiler*](#compilercommand) above.

### env.platform

Return the target platform used for the build (currently the same as the host
platform).

#### platform.flavor

The "flavor" of the platform. Either `'posix'` or `'windows'`.

#### platform.name

The name of the platform, e.g. `'linux'`, `'darwin'` (OS X), or `'windows'`.

## Miscellaneous

### bfg9000_required_version([*version*], [*python_version*])

Set the required *version* for bfg9000 and/or the required *python_version*.
Each of these is a standard Python [version
specifier](https://www.python.org/dev/peps/pep-0440/#version-specifiers).

### bfg9000_version

Return the current version of bfg9000. This can be useful if you want to
optionally support a feature only available in certain versions of bfg.

### filter_by_platform(*name*, *type*)

Return *True* if *name* is a filename that should be included for the target
platform, and *False* otherwise. File (or directory) names like `PLATFORM` or
`foo_PLATFORM.cpp` are excluded if `PLATFORM` is a known platform name that
*doesn't* match the target platform. Known platform names are: `'posix'`,
`'linux'`, `'darwin'`, `'cygwin'`, `'windows'`.

This is the default *filter* for
[*find_files*](find_filespath-name-type-flat-filter-cache).

### find_files([*path*], [*name*], [*type*], [*flat*], [*filter*], [*cache*])

Find files in *path* whose name matches the glob *name*. If *path* is omitted,
search in the root of the source directory; if *name* is omitted, all files will
match. *type* may be either `'f'` to find only files or `'d'` to find only
directories. If *flat* is true, *find_files* will not recurse into
subdirectories. You can also specify a custom *filter* function to filter the
list of files; this function takes two arguments: the file's name and its type.

Finally, if *cache* is *True* (the default), this lookup will be cached so that
any changes to the result of this function will regenerate the build scripts
for the project. This allows you do add or remove source files and not have to
worry about manually rerunning bfg9000.
