# Reference

Below are listed all the builtin functions and properties available to bfg9000
scripts (`build.bfg` and `build.opts`). Most are only available to `build.bfg`
files, since that's where most of the build configuration logic belongs, but
some may be used in `build.opts`. Consult each function to see its availability.

## File types

Files used in a `build.bfg` script are divided by their types (e.g. source
code, header files, etc). All files from the source directory which are
referenced in the `build.bfg` script will automatically be added to the source
distribution when it's built.

In most cases, you can simply pass a string to functions expecting a file type;
the string will automatically be converted to a file object of the appropriate
type. However, in some cases, you may wish to explicitly create a file object.
This can be useful, for instance, when running commands that take a source file
as an argument, e.g. in the following snippet:

```python
command('script', cmd=['python', source_file('script.py')])
```

Using [*source_file*](#source_filename-lang) here allows you to specify that the
file is found in the *source directory*, rather than the build directory.

### directory(*name*, [*include*], [*exclude*], [*filter*]) { #directory }
Availability: `build.bfg`
{: .subtitle}

Create a reference to an existing directory named *name*. This allows you to
refer to an arbitrary subfolder of your source directory. The arguments
*include*, *exclude*, and *filter* are as per [*find_files*](#find_files). Any
matching files will be added to the project's [source
distribution](writing.md#distributing-your-source).

### extra_dist([*files*], [*dirs*]) { #extra_dist }
Availability: `build.bfg`
{: .subtitle}

Add extra *files* and *dirs* to the list of recognized source files. This lets
you reference files that are part of the source distribution but which have no
impact on the build proper (e.g. READMEs).

### generic_file(*name*) { #generic_file }
Availability: `build.bfg`
{: .subtitle}

Create a reference to an existing file named *name*.

### header_directory(*name*, [*include*], [*exclude*], [*filter*], [*system*]) { #header_directory }
Availability: `build.bfg`
{: .subtitle}

Create a reference to a directory named *name* containing header files for the
project. This can then be used in the *include* argument when
[compiling](#object_file) a source file. The arguments *include*, *exclude*, and
*filter* are as per [*find_files*](#find_files). Any matching files will be
added to the project's [source
distribution](writing.md#distributing-your-source).

If *system* is *True*, this directory will be treated as a
[system directory](https://gcc.gnu.org/onlinedocs/cpp/System-Headers.html) for
compilers that support this.

### header_file(*name*) { #header_file }
Availability: `build.bfg`
{: .subtitle}

Create a reference to an existing header named *name*. This is useful if you'd
like to [install](#install) a single header file for your project.

### source_file(*name*, [*lang*]) { #source_file }
Availability: `build.bfg`
{: .subtitle}

Create a reference to an existing source file named *name*. If *lang* is not
specified, the language of the file is inferred from its extension.

## Build steps
Availability: `build.bfg`
{: .subtitle}

Build steps define rules to create an output (usually a file) from zero or more
inputs (also usually files). As you may expect, if the output doesn't exist, the
step is run to generate it. Each input is a dependency on the output, and any
changes to an input will result in a rebuild. This includes headers `#include`d
by any of the source files, but does *not* include files external to the project
(i.e. [packages](#package-resolvers)).

In addition, all build steps have the ability to define extra dependencies via
the *extra_deps* argument. These can be files or other build steps, and changes
to them will trigger a rebuild as with the build's inputs.

Finally, build steps which produce a file can also be used like the
[file types](#file-types) described above to refer to prebuilt files already in
the source tree (e.g. static libraries provided in binary form by a
vendor). This is described in more detail for each step below.

!!! note
    For build steps which produce a file, the exact name of the output file is
    determined by the platform you're running on. For instance, when building an
    executable file named "foo" on Windows, the resulting file will be
    `foo.exe`.

### build_step(*name*, *cmd*|*cmds*, [*environment*], [*type*], [*args*], [*kwargs*], [*extra_deps*]) { #build_step }
Availability: `build.bfg`
{: .subtitle}

Create a custom build step that produces a file named *name* by running an
arbitrary command (*cmd* or *cmds*). *name* may either be a single file name or
a list of file names. For a description of the arguments *cmd*, *cmds*, and
*environment*, see [*command*](#command) below.

By default, this function return a [*source_file*](#source_file); you can adjust
this with the *type* argument. This should be either 1) a function returning a
file object, or 2) an object with a `.type` attribute that meets the criteria of
(1). You can also pass *args* and *kwargs* to forward arguments along to this
function.

### command(*name*, *cmd*|*cmds*, [*environment*], [*extra_deps*]) { #command }
Availability: `build.bfg`
{: .subtitle}

Create a build step named *name* that runs a list of arbitrary commands,
specified in either *cmd* or *cmds*; *cmd* takes a single command, whereas
*cmds* takes a list of commands. Each command may either be a string to be
parsed according to shell rules or a list of arguments to be passed directly to
the process.

You may also pass a dict to *environment* to set environment variables for the
commands. These override any environment variables set on the command line.

### executable(*name*, [*files*, ..., [*extra_deps*]]) { #executable }
Availability: `build.bfg`
{: .subtitle}

Create a build step that builds an executable file named *name*. *files* is the
list of source (or object) files to link. If an element of *files* is a source
file (or a plain string), this function will implicitly call
[*object_file*](#object_file) on it.

The following arguments may also be specified:

* *include*: Forwarded on to [*object_file*](#object_file)
* *pch*: Forwarded on to [*object_file*](#object_file)
* *libs*: A list of library files (see *shared_library* and *static_library*)
* *packages*: A list of external [packages](#package-finders); also forwarded on
  to *object_file*
* *compile_options*: Forwarded on to [*object_file*](#object_file) as *options*
* *link_options*: Command-line options to pass to the linker
* *lang*: Forwarded on to [*object_file*](#object_file)

If neither *files* nor *libs* is specified, this function merely references an
*existing* executable file (a precompiled binary, a shell script, etc) somewhere
on the filesystem. In this case, *name* is the exact name of the file, relative
to the source directory. This allows you to refer to existing executables for
other functions. In addition, the following arguments may be specified:

* *format*: The object format of the exectuable; by default, this is the
  platform's native object format (e.g. `'elf'` on Linux)

This build step recognizes the [dynamic linking environment
variables](environment-vars.md#dynamic-linking) and the [compiler environment
variable](environment-vars.md#compilation-variables) (e.g. `CC`) for the
relevant language.

### object_file([*name*], [*file*, ..., [*extra_deps*]]) { #object_file }
Availability: `build.bfg`
{: .subtitle}

Create a build step that compiles a source file named *file* to an object file
named *name*; if *name* is not specified, it takes the file name in *file*
without the extension.

The following arguments may also be specified:

* *include*: A list of [directories](#header_directory) to search for header
  files; you may also pass [header files](#header), and their directories will
  be added to the search list
* *pch*: A [precompiled header](#precompiled_header) to use during compilation
* *libs*: A list of library files (see *shared_library* and *static_library*);
  this is only used by languages that need libraries defined at compile-time,
  such as Java
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

### object_files(*files*, ..., [*extra_deps*]) { #object_files }
Availability: `build.bfg`
{: .subtitle}

Create a compilation build step for each of the files in *files*; this is
equivalent to calling [*object_file*](#object_file) for each element in *files*.

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

### precompiled_header([*name*], [*file*, ..., [*extra_deps*]]) { #precompiled_header }
Availability: `build.bfg`
{: .subtitle}

Create a build step that generates a precompiled header, which can be used to
speed up the compilation of [object files](#object_file). If *name* is not
specified, it is inferred from the value of *file*; the exact name varies based
on the compiler being used, but typically looks like `header.hpp.pch` for
cc-like compilers and `header.pch` for MSVC-like compilers.

The arguments for *precompiled_header* are the same as for
[*object_file*](#object_file), with the following additional argument:

* *pch_source*: The source file to be used when building the precompiled
  header. If this is not specified, a source file will automatically be created,
  containing nothing but `#include "header"`, where *header* is the name of the
  header specified in *file*. This option only applies to MSVC-like compilers;
  for all others, it is ignored.

If *file* isn't specified, this function merely references an *existing*
precompiled header somewhere on the filesystem. In this case, *name* must be
specified and is the exact name of the file, relative to the source directory.
In addition, the following argument may be specified:

* *lang*: The source language of the file; if none is specified, defaults to
  `'c'`

!!! warning
    The exact behavior of precompiled headers varies according to the compiler
    you're using. In [GCC][gcc-pch] and [Clang][clang-pch], the header to be
    precompiled must be the *first* file `#include`d in each source file. In
    [MSVC][msvc-pch], the resulting precompiled header is actually compiled
    within the context of a particular source file and will contain all the
    code *up to and including* the header in question.

[gcc-pch]: https://gcc.gnu.org/onlinedocs/gcc/Precompiled-Headers.html
[clang-pch]: http://clang.llvm.org/docs/UsersManual.html#usersmanual-precompiled-headers
[msvc-pch]: https://msdn.microsoft.com/en-us/library/szfdksca.aspx

### shared_library(*name*, [*files*, ..., [*extra_deps*]]) { #shared_library }
Availability: `build.bfg`
{: .subtitle}

Create a build step that builds a shared library named *name*. Its arguments are
the same as [*executable*](#executable), with the following additional argument:

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

### static_library(*name*, [*files*, ..., [*extra_deps*]]) { #static_library }
Availability: `build.bfg`
{: .subtitle}

Create a build step that builds a static library named *name*. Its arguments are
the same as [*executable*](#executable). Link-related arguments (*link_options*,
*libs*, and libraries from *packages*) have no direct effect on this build
step. Instead, they're cached and forwarded on to any dynamic linking step that
uses this static library.

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

### whole_archive(*name*, [*files*, ..., [*extra_deps*]]) { #whole_archive }
Availability: `build.bfg`
{: .subtitle}

Create a build step that builds a [whole-archive](http://linux.die.net/man/1/ld)
named *name*. Whole archives ensures that *every* object file in the library is
included, rather than just the ones whose symbols are referenced. This is
typically used to turn a static library into a shared library.

*whole_archive*'s arguments are the same as for
[*static_library*](#static_library). In addition, you can pass an existing
static library to *whole_archive* to convert it into a whole archive.

!!! warning
    The MSVC linker doesn't have a way of expressing the required directives, so
    *whole_archive* can't be used with it.

## Grouping rules

### alias(*name*, [*deps*]) { #alias }
Availability: `build.bfg`
{: .subtitle}

Create a build step named *name* that performs no actions on its own. Instead,
it just runs its dependencies listed in *deps* as necessary. This build step is
useful for grouping common steps together.

### default(*...*) { #default }
Availability: `build.bfg`
{: .subtitle}

Specify a list of build steps that should be run by default when building. These
are all accumulated into the `all` target. If *default* is never called, all
executables and libraries *not* passed to [*test*](#test) will be built by
default.

### install(*...*) { #install }
Availability: `build.bfg`
{: .subtitle}

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

### global_options(*options*, *lang*) { #global_options }
Availability: `build.bfg`
{: .subtitle}

Specify some *options* (either as a string or list) to use for all compilation
steps for the language *lang*.

### global_link_options(*options*) { #global_link_options }
Availability: `build.bfg`
{: .subtitle}

Specify some *options* (either as a string or list) to use for all link steps
(i.e. for [executables](#executable) and [shared libraries](#shared_library)).

## Test rules

These rules help you define automated tests that can all be run via the `test`
target. For simple cases, you should only need the [*test*](#test) rule, but you
can also wrap your tests with a separate driver using
[*test_driver*](#test_driver).

For cases where you only want to *build* the tests, not run them, you can use
the `tests` target.

### test(*test*, [*options*], [*environment*|*driver*]) { #test }
Availability: `build.bfg`
{: .subtitle}

Create a test for a single test file named *test*. You may specify additional
command-line arguments to the test in *options*. You can also pass temporary
environment variables as a dict via *environment*, or specify a test driver to
add this test file to via *driver*.

### test_driver(*driver*, [*options*], [*environment*|*parent*]) { #test_driver }
Availability: `build.bfg`
{: .subtitle}

Create a test driver which can run a series of tests, specified as command-line
arguments to the driver. You may specify driver-wide command-line arguments via
*options*. You can also pass temporary environment variables as a dict with
*environment*, or specify a parent test driver to wrap this driver via *driver*.

### test_deps(*...*) { #test_deps }
Availability: `build.bfg`
{: .subtitle}

Specify a list of dependencies which must be satisfied before the tests can be
run.

## Package resolvers

### boost_package([*name*], [*version*]) { #boost_package }
Availability: `build.bfg`
{: .subtitle}

Search for a [Boost](https://www.boost.org/) library. You can specify *name* (as
a string or a list) to specify a specific Boost library (or libraries); for
instance, `'program_options'`. For header-only libraries, you can omit *name*.
If *version* is specified, it will ensure that the installed version of Boost
meets the version requirement; it must be formatted as a Python [version
specifier](https://www.python.org/dev/peps/pep-0440/#version-specifiers).

This rule recognizes the following environment variables:
[`BOOST_ROOT`](environment-vars.md#boost_root),
[`BOOST_INCLUDEDIR`](environment-vars.md#boost_includedir),
[`BOOST_LIBRARYDIR`](environment-vars.md#boost_librarydir),
[`CPATH`](environment-vars.md#cpath),
[`INCLUDE`](environment-vars.md#include),
[`LIB`](environment-vars.md#lib),
[`LIBRARY_PATH`](environment-vars.md#library_path).

### package(*name*, [*lang*], [*kind*], [*header*], [*version*]) { #package }
Availability: `build.bfg`
{: .subtitle}

Search for a package named *name*. *lang* is the source language of the library
(`'c'` by default); this will affect how the package is resolved. For native
libraries (C, C++, Fortran, etc), this will use
[`pkg-config`](https://www.freedesktop.org/wiki/Software/pkg-config/) to resolve
the package if it's installed. Otherwise (or if `pkg-config` can't find the
package), this will check the system's default library locations.

You can also specify *kind* to one of `'any'` (the default), `'shared'`, or
`'static'`. This allows you to restrict the search to find only static versions
of a library, for example.

The *header* argument allows you to specify a header file (or list
thereof) that you need to use in your source files. This will search for the
header file and add the appropriate include directory to your build
configuration. (Note: this doesn't apply when `pkg-config` resolves the package,
since `pkg-config` should add the appropriate include directories on its own.)

Finally, if *version* is specified, it will (if possible) ensure that the
installed version of the package meets the version requirement; it must be
formatted as a Python [version
specifier](https://www.python.org/dev/peps/pep-0440/#version-specifiers).

This rule recognizes the following environment variables:
[`CPATH`](environment-vars.md#cpath),
[`INCLUDE`](environment-vars.md#include),
[`LIB`](environment-vars.md#lib),
[`LIBRARY_PATH`](environment-vars.md#library_path),
[`PKG_CONFIG`](environment-vars.md#pkg_config).

### system_executable(*name*) { #system_executable }
Availability: `build.bfg`
{: .subtitle}

Search for an executable named *name* somewhere in the system's PATH.

This rule recognizes the following environment variables:
[`PATH`](environment-vars.md#path), [`PATHEXT`](environment-vars.md#pathext).

## Environment

The *environment*, `env`, is a special object that encapsulates information
about the system outside of bfg9000. It's used internally for nearly all
platform-specific code, but it can also help in `build.bfg` files when you
encounter some unavoidable issue with multiplatform compatibility.

!!! note
    This listing doesn't cover *all* available functions on the environment,
    since many are only useful to internal code. However, the most relevant ones
    for `build.bfg` files are shown below.

### env.builder(*lang*) { #env-builder }
Availability: `build.bfg` and `build.opts`
{: .subtitle}

Return the builder used by bfg9000 for a particular language *lang*. While
builder objects are primarily suited to bfg's internals, there are still a few
useful properties for `build.bfg` files:

#### builder.flavor { #builder-flavor }

The "flavor" of the builder, i.e. the kind of command-line interface it has.
Possible values are `'cc'` and `'msvc'`.

#### builder.brand { #builder-brand }

The brand of the builder, i.e. the commonad name people use for it. Possible
values are `'gcc'`, `'clang'`, `'msvc'`, and `'unknown'`.

#### builder.compiler { #builder-compiler }

The compiler used with this builder.

##### compiler.command { #compiler-command }

The command to run when invoking this compiler, e.g. `g++-4.9`.

#### builder.linker(*mode*) { #builder-linker }

The linker used with this builder. *mode* is one of `'executable'`,
`'shared_library'`, or `'static_library'`. Its public properties are the same as
[*compiler*](#compiler-command) above.

### env.platform { #env-platform }
Availability: `build.bfg` and `build.opts`
{: .subtitle}

Return the target platform used for the build (currently the same as the host
platform).

#### platform.flavor { #platform-flavor }

The "flavor" of the platform. Either `'posix'` or `'windows'`.

#### platform.name { #platform-name }

The name of the platform, e.g. `'linux'`, `'darwin'` (OS X), or `'windows'`.

## Utilities

### argument(*names*..., [*action*], [*nargs*], [*const*], [*default*], [*type*], [*choices*], [*required*], [*help*], [*metavar*], [*dest*]) { #argument }
Availability: `build.opts`
{: .subtitle}

Define how a particular command-line argument will be parsed. *names* is a
sequence of argument names; these will be prefixed with `--` and `--x-` for
parsing. For example, passing `'foo'` will add `--foo` and `--x-foo` as possible
command-line arguments.

All other arguments to this function have the same behavior as in
[*argparse.ArgumentParser.add_argument()*][add_argument], with the exception of
*action*, which accepts two extra values:

* `'enable'`: Add a pair of arguments of the form `--enable-<name>` and
  `--disable-<name>` (with `--x-`-prefixed versions as well), storing *True* if
  `--enable-<name>` is specified and *False* if `--disable-<name>` is.
* `'with'`: As `'enable'`, except the arguments are of the form `--with-<name>`
  and `--without-name`.

[add_argument]: https://docs.python.org/library/argparse.html#the-add-argument-method

### argv
Availability: `build.bfg`
{: .subtitle}

Retrieve the set of [user-defined arguments](writing.md#user-defined-arguments)
passed to bfg9000; this is an [*argparse.Namespace*][namespace] object.

[namespace]: https://docs.python.org/library/argparse.html#argparse.Namespace

### \__bfg9000__
Availability: `build.bfg` and `build.opts`
{: .subtitle}

A dictionary containing all the builtin functions and global variables defined
by bfg9000. This can be useful for feature detection or accessing builtins
shadowed by a local variable.

### bfg9000_required_version([*version*], [*python_version*]) { #bfg9000_required_version }
Availability: `build.bfg` and `build.opts`
{: .subtitle}

Set the required *version* for bfg9000 and/or the required *python_version*.
Each of these is a standard Python [version
specifier](https://www.python.org/dev/peps/pep-0440/#version-specifiers).

### bfg9000_version
Availability: `build.bfg` and `build.opts`
{: .subtitle}

Return the current version of bfg9000. This can be useful if you want to
optionally support a feature only available in certain versions of bfg.

### filter_by_platform(*name*, *path*, *type*) { #filter_by_platform }
Availability: `build.bfg`
{: .subtitle}

Return *FindResult.include* if *path* is a filename that should be included for
the target platform, and *FindResult.not_now* otherwise. File (or directory)
names like `PLATFORM` or `foo_PLATFORM.cpp` are excluded if `PLATFORM` is a
known platform name that *doesn't* match the target platform. Known platform
names are: `'posix'`,`'linux'`, `'darwin'`, `'cygwin'`, `'windows'`.

This is the default *filter* for [*find_files*](#find_files).

### FindResult
Availability: `build.bfg`
{: .subtitle}

An enum to be used as the result of a filter function for
[*find_files*](#find_files). The possible enum values are:

* *include*: Include this file in the results
* *exclude*: Don't include this file in the results
* *not_now*: Don't include this file in the results, but do include it in the
  [source distribution](writing.md#distributing-your-source)

### find_files([*path*], [*name*], [*type*], [*extra*], [*exclude*], [*flat*], [*filter*], [*cache*], [*dist*], [*as_object*]) { #find_files }
Availability: `build.bfg`
{: .subtitle}

Find files in *path* whose name matches the glob (or list of globs) *name*. The
following arguments may be specified:

* *path*: A path (or list of paths) to start the search in; if omitted, search
  in the root of the source directory (`'.'`)
* *name*: A glob (or list of globs) to match files; if omitted, all files match
  (equivalent to `'*'`)
* *type*: A filter for the type of file: `'f'` to find only files, `'d'` to find
  only directories, or `'*'` to find either
* *extra*: A glob (or list of globs) to match extra files (which will not be
  returned from *find_files* but will be added to the
  [source distribution](writing.md#distributing-your-source))
* *exclude*: A glob (or list of globs) of files to exclude from results; by
  default, `.#*`, `*~`, and `#*#` are exluded
* *flat*: If true, *find_files* will not recurse into subdirectories; otherwise,
  (the default) it will
* *filter*: A predicate taking a filename, relative path, and file type, and
  returning a [*FindResult*](#FindResult) which will filter the results; by
  default, this is [*filter_by_platform*](#filter_by_platform)
* *cache*: If true (the default), cache the results so that any changes to will
  regenerate the build scripts for the project
* *dist*: If true (the default), all files found by this function will
  automatically be added to the source distribution
* *as_object*: If true, results will be returned as file or directory objects;
  otherwise (the default), return path strings

The *cache* argument is particularly important. It allows you to add or remove
source files and not have to worry about manually rerunning bfg9000.

### project(*name*, [*version*]) { #project }
Availability: `build.bfg`
{: .subtitle}

Set the name (and optionally the version) of the project. If you don't call
this function to specify a project name, it defaults to the name of the
project's source directory. This is primarily useful for creating [source
distributions](writing.md#distributing-your-source).
