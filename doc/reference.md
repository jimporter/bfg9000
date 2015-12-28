# Reference

## File types

### header(*name*)

Create a reference to an existing header named *name*. This is useful if you'd
like to [install](#install-all) a single header file for your project.

### header_directory(*directory*, [*system*])

Create a reference to a *directory* containing header files for the project.
This can then be used in the *include* argument when
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

!!! note
    For build steps which produce an actual file, the exact name of the output
    file is determined by the platform you're running on. For instance, when
    building an executable file named "foo" on Windows, the resulting file will
    be `foo.exe`.

### alias(*name*, [*deps*])

Create a build step named *name* that performs no actions on its own. Instead,
it just runs its dependencies listed in *deps* as necessary. This build step is
useful for grouping common steps together, e.g. the common `make all` command.

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
[*object_file*](object_filename-file-extra_deps) on it.

The following arguments may also be specified:

* *include*: Forwarded on to [*object_file*](object_filename-file-extra_deps)
* *libs*: A list of library files (see *shared_library* and *static_library*)
* *packages*: A list of external [packages](#package-finders); also forwarded on
  to *object_file*
* *compile_options*: Forwarded on to
  [*object_file*](object_filename-file-extra_deps) as *options*
* *link_options*: Command-line options to pass to the linker
* *lang*: Forwarded on to [*object_file*](object_filename-file-extra_deps)

If *files* isn't specified, this function merely references an *existing*
executable file (a precompiled binary, a shell script, etc) somewhere on the
filesystem. In this case, *name* is the exact name of the file. This allows
you to refer to existing executables for other functions.

This build step recognizes the following environment variables:
[`CC`](environment-vars.md#cc), [`CC_LINK`](environment-vars.md#cc_link),
[`CXX`](environment-vars.md#cxx), [`CXX_LINK`](environment-vars.md#cxx_link),
[`LDFLAGS`](environment-vars.md#ldflags),
[`LDLIBS`](environment-vars.md#ldlibs).

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
and is the exact name of the file.

This build step recognizes the following environment variables:
[`CC`](environment-vars.md#cc), [`CFLAGS`](environment-vars.md#cflags),
[`CPPFLAGS`](environment-vars.md#cppflags), [`CXX`](environment-vars.md#cxx),
[`CXXFLAGS`](environment-vars.md#cxxflags),
[`LDLIBS`](environment-vars.md#ldlibs).

### object_files(*files*, ..., [*extra_deps*])

Create a compilation build step for each of the files in *files*; this is
equivalent to calling [*object_file*](#object_filename-file-extra_deps) for each
element in *files*.

### shared_library(*name*, [*files*, ..., [*extra_deps*]])

Create a build step that builds a shared library named *name*. Its arguments are
the same as [*executable*](#executablename-files-extra_deps).

This build step recognizes the following environment variables:
[`CC`](environment-vars.md#cc), [`CC_LINK`](environment-vars.md#cc_link),
[`CXX`](environment-vars.md#cxx), [`CXX_LINK`](environment-vars.md#cxx_link),
[`LDFLAGS`](environment-vars.md#ldflags),
[`LDLIBS`](environment-vars.md#ldlibs).

!!! note
    On Windows, this produces *two* files: `name.dll` and `name.lib`. The latter
    is the *import library*, used when linking to this library. As a result,
    `my_lib.all` returns a list containing two files.

### static_library(*name*, [*files*, ..., [*extra_deps*]])

Create a build step that builds a static library named *name*. Its arguments are
the same as [*executable*](#executablename-files-extra_deps).

This build step recognizes the following environment variables:
[`AR`](environment-vars.md#ar), [`ARFLAGS`](environment-vars.md#arflags),
[`CC_LIB`](environment-vars.md#cc_lib),
[`CXX_LIB`](environment-vars.md#cxx_lib),
[`LIBFLAGS`](environment-vars.md#libflags).

## Grouping rules

### default(*...*)

Specify a list of build steps that should be run by default when building. These
are all accumulated into the `all` target.

### install(*...*, [*all*])

Specify a list of files that need to be installed for the project to work. Each
will be installed to the appropriate location based on its type (e.g. header
files will go in `$PREFIX/include` by default on POSIX systems). These are all
accumulated into the `install` target.

If *all* is *True*, all the files will be installed; otherwise, only the primary
file for each argument will be. For instance, on Windows, this means that
setting *all* to *True* installs the import libraries as well as the DLLs for
shared libraries.

This rule recognizes the following environment variables:
[`INSTALL`](environment-vars.md#install),
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

## Package finders

### boost_package([*name*], [*version*])

Search for a Boost library. You can specify *name* (as a string or a list) to
specify a specific Boost library (or libraries); for instance,
`'program_options'`. For header-only libraries, you can omit *name*.

This rule recognizes the following environment variables:
[`BOOST_ROOT`](environment-vars.md#boost_root),
[`BOOST_INCLUDEDIR`](environment-vars.md#boost_includedir),
[`BOOST_LIBRARYDIR`](environment-vars.md#boost_librarydir).

### system_executable(*name*)

Search for an executable named *name* somewhere in the system's PATH.

This rule recognizes the following environment variables:
[`PATH`](environment-vars.md#path), [`PATHEXT`](environment-vars.md#pathext).

### system_package(*name*, [*kind*])

Search for a library named *name* somewhere in the system's default library
location. You can specify *kind* to one of `'any'` (the default), `'shared'`,
or `'static'`. This allows you to restrict the search to find only static
versions of a library, for example.

This rule recognizes the following environment variables:
[`LIBRARY_PATH`](environment-vars.md#library_path).

!!! note
    This only finds the library itself, not any required headers. Those are
    assumed to be somewhere where your compiler can find them automatically; if
    not, you can set [`CPPFLAGS`](environment-vars.md#cppflags) to add the
    appropriate header search path.

## Miscellaneous

### bfg9000_required_version([*version*], [*python_version*])

Set the required *version* for bfg9000 and/or the required *python_version*.
Each of these is a standard Python [version
specifier](https://www.python.org/dev/peps/pep-0440/#version-specifiers).

### filter_by_platform(*name*, *type*)

Return *True* if *name* is a filename that should be included for the target
platform, and *False* otherwise. File (or directory) names like `PLATFORM` or
`foo_PLATFORM.cpp` are excluded if `PLATFORM` is a known platform name that
*doesn't* match the target platform. Known platform names are: *posix*,
*linux*, *darwin*, *cygwin*, *windows*.

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
