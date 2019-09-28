# Reference

Below are listed all the builtin functions and properties available to bfg9000
scripts (`build.bfg` and `options.bfg`). Most are only available to `build.bfg`
files, since that's where most of the build configuration logic belongs, but
some may be used in `options.bfg`. Consult each function to see its
availability.

## General

### Representing paths

While all platforms have paths, their representation varies from platform to
platform. bfg9000 smooths over these differences by providing a cross-platform
representation of paths. Both POSIX- and Windows-style paths are supported and
will be translated to a standard internal representation before being emitted to
build scripts in their platform-specific form. Thus, `foo/bar` and `foo\bar` are
equivalent to bfg9000.

!!! note
    While absolute paths are rarely needed in a `build.bfg` script, it's still
    possible to use them. However, there are some caveats: 1) POSIX-style
    absolute paths will refer to that (absolute) path on the *current* drive,
    2) Windows-style absolute paths will fail to work on POSIX systems, and 3)
    Windows-style paths with a drive letter and a *relative* path (e.g. `C:foo`)
    are unsupported by bfg9000.

## File objects

Files used in a `build.bfg` script are divided by their types (e.g. source
code, header files, etc). All files from the source directory which are
referenced in the `build.bfg` script will automatically be added to the source
distribution when it's built.

In most cases, you can simply pass a string to functions expecting a file
object; the string will automatically be converted to a file object of the
appropriate type. However, in some cases, you may wish to explicitly create a
file object. This can be useful, for instance, when running commands that take a
source file as an argument, e.g. in the following snippet:

```python
command('script', cmd=[source_file('script.py')])
```

Using [*source_file*](#source_file) here allows you to specify that the file is
a source code file found in the *source directory*, rather than the build
directory. Further, since the file is a Python script, it can be executed as
part of a [*command*](#command) step.

In addition to the functions listed in this section below,
[build steps](#build_step) which generate a file can also be used to produce
source files of that type (see each step's documentation for details).

### auto_file(*name*, [*lang*]) { #auto_file }

Create a reference to an existing file named *name*. This function will try to
automatically determine the file's kind based on its extension:
[*source_file*](#source_file); [*header_file*](#header_file);
[*resource_file*](#resource_file); or, if the extension is not recognized,
[*generic_file*](#generic_file). If *lang* is specified, files with an
unrecognized extension will always be treated as [*source_file*](#source_file)s.

!!! note
    This function is primarily useful for writing generic code that works with
    multiple kinds of files; when creating a reference to a specific, *known*
    file, the concrete function listed above should be used instead.

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

If *system* is *True*, this directory will be treated as a [system
directory][system-directory] for compilers that support this.

### header_file(*name*) { #header_file }
Availability: `build.bfg`
{: .subtitle}

Create a reference to an existing header named *name*. This is useful if you'd
like to [install](#install) a single header file for your project.

### module_def_file(*name*) { #module_def_file }
Availability: `build.bfg`
{: .subtitle}

Create a reference to an existing module-definition file named *name*.
[Module-definition files][def-file] are sometimes used when building libraries
on Windows.

### resource_file(*name*, [*lang*]) { #resource_file }
Availability: `build.bfg`
{: .subtitle}

Create a reference to an existing resource file named *name*. If *lang* is not
specified, the language of the file is inferred from its extension.

### source_file(*name*, [*lang*]) { #source_file }
Availability: `build.bfg`
{: .subtitle}

Create a reference to an existing source file named *name*. If *lang* is not
specified, the language of the file is inferred from its extension.

## Build steps

Build steps describe how to create a target output (usually a file) from zero or
more inputs (usually files or other build steps). As you may expect, if the
output is a file and it's either out of date or doesn't exist, the step is run
to generate it. Each input is a dependency on the output, and any changes to an
input will result in a rebuild. This includes headers `#include`d by any of the
source files, but does *not* include files external to the project (i.e.
[packages](#package-resolvers)).

Most build steps also have the ability to define additional dependencies via the
*extra_deps* argument. These can be files or other build steps, and changes to
them will trigger a rebuild as with the build's inputs.

Further, many build steps also allow setting a custom *description*. This can be
used to provide a friendlier message for the Ninja backend to show when building
that step.

## File steps

Naturally, the most common type of build step is one that generates a file.
These are responsible for compiling object files, linking executables and
libraries, and so on. In addition, all of these steps can be used like the [file
object](#file-objects) functions described above to refer to prebuilt files
already in the source tree (e.g. static libraries provided in binary form by a
vendor). This is described in more detail for each step below.

!!! note
    For file steps, the exact name of the output file is determined by the
    platform you're running on. For instance, when building an executable file
    named "foo" on Windows, the resulting file will be `foo.exe`.

### copy_file([*name*], *file*, [*mode*], [*extra_deps*], [*description*]) { #copy_file }
Availability: `build.bfg`
{: .subtitle}

Create a build step that copies a file named *file* to a destination named
*name*; if *name* is not specified, this function will use the filename in
*file* as a base (this is primarily useful for copying a file from the source
directory to the build directory). *mode* specifies how the file should be
copied: `'copy'`, `'symlink'`, or `'hardlink'`.

This build step recognizes the [environment
variables](environment-vars.md#command-variables) for the relevant copy mode.

### copy_files(*files*, [*mode*], [*extra_deps*], [*description*]) { #copy_files }
Availability: `build.bfg`
{: .subtitle}

Create a build step to copy each of the files in *files* using the specified
*mode*; this is equivalent to calling [*copy_file*](#copy_file) for each element
in *files*.

Like [*object_files*](#object_files), *copy_files* returns a special list that
allows you to index into it using the filename of one of the source files listed
in *files*.

### executable(*name*, [*files*, ..., [*extra_deps*], [*description*]]) { #executable }
Availability: `build.bfg`
{: .subtitle}

Create a build step that builds an executable file named *name*. *files* is the
list of source (or object) files to link. If an element of *files* is a source
file (or a plain string), this function will implicitly call
[*object_file*](#object_file) on it.

The following arguments may also be specified:

* *includes*: Forwarded on to [*object_file*](#object_file)
* *pch*: Forwarded on to [*object_file*](#object_file)
* *libs*: A list of library files (see *shared_library* and *static_library*)
* *packages*: A list of external [packages](#package-finders); also forwarded on
  to *object_file*
* *compile_options*: Forwarded on to [*object_file*](#object_file) as *options*
* *link_options*: Command-line options to pass to the linker
* *module_defs*: A [*module_def_file*](#module_def_file) specifying information
  about exports and other program info, sometimes used on Windows
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

!!! note
    When passing options to the linker via `link_options`, these options will be
    passed to whatever executable is typically used to link object files for the
    source language; in particular, this means that when using a tool like GCC
    to build your project, any linker options that need to be forwarded on to
    `ld` should be prepended with `'-Wl,'`.

### generated_source([*name*], *file*, ..., [*extra_deps*], [*description*]) { #generated_source }
Availability: `build.bfg`
{: .subtitle}

Create a build step that generates a source file named *name* from an input
(typically another source file) named *file*; if *name* is not specified, this
function will use the filename in *file* as a base (typically the filename with
a different extension). Note that unlike with other file steps, *name*
represents the exact file name to be used for the output file (i.e. the file
extension isn't added automatically).

The following arguments may also be specified:

* *options*: Command-line options to pass to the compiler
* *lang*: The language of the source file; useful if the source file's extension
  isn't recognized by bfg9000

!!! note
    When building files via `yacc`, this step will automatically generate both
    source and header files named `<name>.tab.c` and `<name>.tab.h`. You can
    force this step to build only the source file by passing a single filename
    to the *name* argument; you can also customize the names by passing a pair
    of filenames: `generated_source(['foo.c', 'foo.h'], 'bar.y')`

This build step recognizes the [compilation environment
variables](environment-vars.md#compilation-variables) for the relevant language.

### generated_sources(*files*, ..., [*extra_deps*], [*description*]) { #generated_sources }
Availability: `build.bfg`
{: .subtitle}

Create a source-generation build step for each of the files in *files*; this is
equivalent to calling [*generated_source*](#generated_source) for each element
in *files*.

Like [*object_files*](#object_files), *generated_sources* returns a special list
that allows you to index into it using the filename of one of the source files
listed in *files*.

### library(*name*, [*files*, ..., [*extra_deps*], [*description*]]) { #library }
Availability: `build.bfg`
{: .subtitle}

Create a build step that builds a shared library named *name*. Its arguments are
the same as the superset of [*shared_library*](#shared_library) and
[*static_library*](#static_library), with the following additional argument:

* *kind*: The kind of library to be built; one of [`'shared'`](#shared_library),
  [`'static'`](#static_library), or `'dual'` (to build both shared *and* static
  versions). If not specified, the default behavior depends on the command-line
  arguments passed to bfg9000. To enable/disable shared libraries, pass
  `--enable-shared`/`--disable-shared`, and for static libraries, pass
  `--enable-static`/`--disable-static`.

Like with *executable*, if *files* isn't specified, this function merely
references an *existing* library somewhere on the filesystem. In this case,
*name* must be specified and is the exact name of the file, relative to
the source directory. You may also pass in the *format* argument as with
*executable*.

If *name* refers to a dual-use library, this function will return the library
subtype as specified in *kind* (e.g. passing `'shared'` will return the shared
version of the library).

This build step recognizes the [dynamic linking environment
variables](environment-vars.md#dynamic-linking) or the [static
linking environment variables](environment-vars.md#static-linking), as well as
the [compiler environment
variable](environment-vars.md#compilation-variables) (e.g. `CC`) for the
relevant language.

!!! warning
    By convention, MSVC uses the same filenames for static libraries as for
    import libs for shared libraries. As a result, if both shared and static
    library builds are enabled with MSVC, bfg9000 will fall back to building
    only the shared library.

### object_file([*name*], [*file*, ..., [*extra_deps*], [*description*]]) { #object_file }
Availability: `build.bfg`
{: .subtitle}

Create a build step that compiles a source file named *file* to an object file
named *name*; if *name* is not specified, this function will use the filename
in *file* as a base (typically the filename without the extension).

The following arguments may also be specified:

* *includes*: A list of [directories](#header_directory) to search for header
  files; you may also pass [header files](#header_file), and their directories
  will be added to the search list
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

### object_files(*files*, ..., [*extra_deps*], [*description*]) { #object_files }
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

### precompiled_header([*name*], [*file*, ..., [*extra_deps*], [*description*]]) { #precompiled_header }
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

### shared_library(*name*, [*files*, ..., [*extra_deps*], [*description*]]) { #shared_library }
Availability: `build.bfg`
{: .subtitle}

Create a build step that builds a shared library named *name*. Its arguments are
the same as [*executable*](#executable), with the following additional
arguments:

* *version*: The version number of the library, e.g. `1.2.3`.
* *soversion*: The API version of the library (used in its soname), e.g. `1`.

Like with *executable*, if *files* isn't specified, this function merely
references an *existing* shared library somewhere on the filesystem. In this
case, *name* must be specified and is the exact name of the file, relative to
the source directory. You may also pass in the *format* argument as with
*executable*.

If *name* refers to a dual-use library, this function will return the shared
version of the library.

This build step recognizes the [dynamic linking environment
variables](environment-vars.md#dynamic-linking) and the [compiler environment
variable](environment-vars.md#compilation-variables) (e.g. `CC`) for the
relevant language.

!!! note
    On Windows, this produces *two* files for native-runtime languages (e.g. C
    or C++): `name.dll` and `name.lib`. The latter is the *import library*, used
    when linking to this library.

    Additionally for native languages on Windows, this step will add a
    preprocessor macro named `LIB<NAME>_EXPORTS` that can be used for declaring
    public symbols. See [Building libraries on
    Windows](writing.md#building-libraries-on-windows) for an example of how to
    use this macro in your code.

### static_library(*name*, [*files*, ..., [*extra_deps*], [*description*]]) { #static_library }
Availability: `build.bfg`
{: .subtitle}

Create a build step that builds a static library named *name*. Its arguments are
the same as [*executable*](#executable), with the following additional argument:

* *static_link_options*: Command-line options to pass to the linker

Other link-related arguments (*link_options*, *libs*, and libraries from
*packages*) have no direct effect on this build step. Instead, they're cached
and forwarded on to any dynamic linking step that uses this static library.

Like with *executable*, if *files* isn't specified, this function merely
references an *existing* shared library somewhere on the filesystem. In this
case, *name* must be specified and is the exact name of the file, relative to
the source directory. In addition, the following arguments may be specified:

* *format*: The object format of the exectuable; by default, this is the
  platform's native object format (e.g. `'elf'` on Linux)
* *lang*: The source language(s) of the library; if none is specified, defaults
  to `['c']`

If *name* refers to a dual-use library, this function will return the static
version of the library.

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

Create a build step that builds a [whole-archive][whole-archive] named *name*.
Whole archives ensures that *every* object file in the library is included,
rather than just the ones whose symbols are referenced. This is typically used
to turn a static library into a shared library.

*whole_archive*'s arguments are the same as for
[*static_library*](#static_library). In addition, you can pass an existing
static library to *whole_archive* to convert it into a whole archive.

## Test steps

These steps help you define automated tests that can all be run via the `test`
target. For simple cases, you should only need the [*test*](#test) function, but
you can also wrap your tests with a separate driver using
[*test_driver*](#test_driver).

For cases where you only want to *build* the tests, not run them, you can use
the `tests` target.

### test(*test*, [*environment*|*driver*]) { #test }
Availability: `build.bfg`
{: .subtitle}

Create a single test. *cmd* is the base command (possibly with arguments)
to run; this works much like the *cmd* argument in the [*command*](#command)
built-in. You can also pass temporary environment variables as a dict via
*environment*, or specify a test driver to add this test file to via *driver*.

### test_driver(*cmd*, [*environment*|*parent*], [*wrap_children*]) { #test_driver }
Availability: `build.bfg`
{: .subtitle}

Create a test driver which can run a series of tests, specified as command-line
arguments to the driver. *cmd* is the base command (possibly with arguments)
to run; this works much like the *cmd* argument in the [*command*](#command)
built-in. You can also pass temporary environment variables as a dict with
*environment*, or specify a parent test driver to wrap this driver via *parent*.

Finally, you can specify *wrap_children* to determine how tests using this
driver are run. If true, each test will be wrapped by
[*env.run_arguments*](#env-run_arguments); if false (the default), tests will be
used as-is.

### test_deps(*...*) { #test_deps }
Availability: `build.bfg`
{: .subtitle}

Specify a list of extra dependencies which must be satisfied when building the
tests via the `tests` target.

## Grouping steps

### alias(*name*, [*deps*]) { #alias }
Availability: `build.bfg`
{: .subtitle}

Create a build step named *name* that performs no actions on its own. Instead,
it just runs its dependencies listed in *deps* as necessary. This build step is
useful for grouping common steps together.

### default(*...*) { #default }
Availability: `build.bfg`
{: .subtitle}

Specify a list of build outputs that should be run by default when building.
These are all accumulated into the `all` target. If *default* is never called,
all executables and libraries *not* passed to [*test*](#test) will be built by
default. To allow this to be chained with other functions, *default* will return
the arguments passed into it: as a single object if one argument is passed, or
a tuple if multiple are passed.

### install(*...*) { #install }
Availability: `build.bfg`
{: .subtitle}

Specify a list of files that need to be installed for the project to work. Each
will be installed to the appropriate location based on its type, e.g. header
files will go in `$PREFIX/include` by default on POSIX systems. These are all
accumulated into the `install` target. If there are any runtime dependencies for
a file (such as shared libraries you just built), they will be installed as
well. As with [*default*](#default), this function will return the files passed
into it.

!!! note
    When explicitly listing a target, *all* the files for that target will be
    installed. For instance, on Windows, this means that passing in a shared
    library will install the DLL *and* the import library.

This step recognizes the following environment variables:
[`DESTDIR`](environment-vars.md#destdir),
[`INSTALL`](environment-vars.md#install),
[`INSTALL_NAME_TOOL`](environment-vars.md#install_name_tool),
[`MKDIR_P`](environment-vars.md#mkdir_p),
[`PATCHELF`](environment-vars.md#patchelf).

## User-defined steps

While the standard build steps cover the most common tasks in a build, many
projects need to run more-specialized commands. A build script can define custom
steps via the [*build_step*](#build_step) and [*command*](#command) functions:
*build_step* defines a step which outputs one or more files that can be used in
other steps, while *command* defines a more general step that should always be
run when it's a target (similar to the `test` or `install` targets).

Both *build_step* and *command* allow you to specify an arbitrary command *cmd*
or *cmds*; *cmd* takes a single command, whereas *cmds* takes a list of
commands. Each command will be passed through
[*env.run_arguments()*](#env-run_arguments) and may be a string (to be parsed
according to shell rules), a file object (such as an
[*executable*](#executable)), or a list of arguments to be passed directly to
the process. Any file objects specified in the command will automatically be
added as dependencies to this step. In addition, commands can include
[placeholders](#placeholder), which will automatically be expanded to the files
corresponding to that placeholder.


You may also pass a dict to *environment* to set environment variables for the
commands. These override any environment variables set on the command line.

### build_step(*name*, *cmd*|*cmds*, [*files*], [*environment*], [*type*], [*always_outdated*], [*extra_deps*], [*description*]) { #build_step }
Availability: `build.bfg`
{: .subtitle}

Create a custom build step that produces one or more files named *name* by
running an arbitrary command (*cmd* or *cmds*). *name* may either be a single
file name or a list of file names. If *always_outdated* is true, this build step
will be considered out-of-date no matter the status of the output.

The command argument can use the [placeholders](#placeholder)
`build_step.output` to refer to the output files (defined by *name*) and
`build_step.input` to refer to the input files (defined by *files*).

By default, the output of this step is one or more [*auto_file*](#auto_file)s;
you can adjust this with the *type* argument: this should be a function (or a
list thereof) taking a path and returning a file object. If *type* is a single
function, it will be applied to every output of *build_step*; if it's a list of
functions, they will be applied element-wise to each output.

### command(*name*, *cmd*|*cmds*, [*files*], [*environment*], [*extra_deps*], [*description*]) { #command }
Availability: `build.bfg`
{: .subtitle}

Create a build step named *name* that runs an arbitrary command, specified in
either *cmd* or *cmds*. This build step is always considered out-of-date (as
with a "phony" Makefile target, such as `test` or `install`).

The command argument can use the [placeholder](#placeholder) `command.input` to
refer to the input files (defined by *files*).

### *placeholder*
Availability: `build.bfg`
{: .subtitle}

When used in the *cmd* or *cmds* argument of [*build_step*](#build_step) or
[*command*](#command), this will create a reference to the inputs or outputs of
the step. Placeholders can be indexed or sliced just like ordinary Python lists,
and can also be combined with strings to add prefixes and suffixes:

```python
script = source_file('script.py')

# Roughly equivalent to `python script.py -ifoo.txt -sbar.txt -squux.txt`
command('foo', cmd=[
    script, '-i' + command.input[0], '-s' + command.input[1:]
], files=['foo.txt', 'bar.txt', 'quux.txt'])
```

## Semantic options

Semantic options are a collection of objects that allow a build to define
options in a tool-agnostic way. These options will automatically be converted to
the appropriate string form for the tool when generating the build file.

### opts.debug() { #opts-debug }

Produce debugging information for the built object in the default debugging
format.

### opts.define(*name*, [*value*]) { #opts-define }

Create a preprocessor macro named *name* and with an optional value *value*.
Note that if you'd like the value to be a string literal, you need to escape the
string like so:

```python
opts.define('MY_MACRO', '"This is a string, isn\'t it?"')
```

### opts.optimize(*...*) { #opts-optimize }

Set the level of optimization for the compiler employ; multiple values can be
specified at once, e.g. `opts.optimize('speed, 'linktime)`. The possible warning
values are:

* `'disable'`: Disable all optimization
* `'size'`: Enable optimization to minimize the size of the resulting binary
* `'speed'`: Enable optimization to maximize the speed of the resulting binary
* `'linktime'`: Perform link-time optimizations

### opts.sanitize() { #opts-sanitize }

Enable run-time sanitization checks when compiling a particular source file;
this is equivalent to `-fsanitize=address` on GCC-like compilers and `/RTC1` on
MSVC.

### opts.std(*value*) { #opts-std }

Specify the version of the language's standard (e.g. `"c++14"`) to use when
building.

### opts.warning(*...*) { #opts-warning }

Set the level of warnings for the compiler to emit when compiling; multiple
values can be specified at once, e.g. `opts.warning('all', 'error')`. The
possible warning values are:

* `'disable'`: Disable all warning messages
* `'all'`: Enable all "recommended" warnings (as GCC puts it, "the warnings
  about constructions that some users consider questionable, and that are easy
  to avoid")
* `'extra'`: Enable extra warnings in addition to what's specified in `'all'`
* `'error'`: Treat any warning as an error

## Global options

### global_options(*options*, *lang*) { #global_options }
Availability: `build.bfg`
{: .subtitle}

Specify some *options* (either as a string or list) to use for all compilation
steps for the language (or list of languages) *lang*.

### global_link_options(*options*, [*family*], [*mode*]) { #global_link_options }
Availability: `build.bfg`
{: .subtitle}

Specify some *options* (either as a string or list) to use for all link steps
for a given *family* of languages (or a list of families) and linking *mode*.

By default *family* is `'native'`, used for C, C++, and other languages using
the same linking process. You can also specify `'jvm'` for JVM-based languages
(Java, Scala). *mode* may be either `'dynamic'` (the default) to modify
[executables](#executable) and [shared libraries](#shared_library) or `'static'`
to modify [static libraries](#static_library).

!!! note
    As with the `link_options` argument for [*executable()*](#executable) and
    [*shared_library()*](#shared_library), dynamic link options will be passed
    to whatever executable is typically used to link object files for the source
    language; in particular, this means that when using a tool like GCC to build
    your project, any linker options that need to be forwarded on to `ld` should
    be prepended with `'-Wl,'`.

## Package resolvers

### boost_package([*name*], [*version*]) { #boost_package }
Availability: `build.bfg`
{: .subtitle}

Search for a [Boost][boost] library. You can specify *name* (as a string or a
list) to specify a specific Boost library (or libraries); for instance,
`'program_options'`. For header-only libraries, you can omit *name*. If
*version* is specified, it will ensure that the installed version of Boost meets
the version requirement; it must be formatted as a Python [version
specifier][version-specifier].

If this function is unable to find the specified Boost library, it will raise a
[*PackageResolutionError*](#packageresolutionerror). If the library is found but
doesn't match the required version, a
[*PackageVersionError*](#packageversionerror) will be raised instead.

This function recognizes the following environment variables:
[`BOOST_ROOT`](environment-vars.md#boost_root),
[`BOOST_INCLUDEDIR`](environment-vars.md#boost_includedir),
[`BOOST_LIBRARYDIR`](environment-vars.md#boost_librarydir),
[`CPATH`](environment-vars.md#cpath),
[`INCLUDE`](environment-vars.md#include),
[`LIB`](environment-vars.md#lib),
[`LIBRARY_PATH`](environment-vars.md#library_path).

### framework(*name*, [*suffix*]) { #framework }

Reference a macOS [framework][framework] named *name* with the optional suffix
*suffix*. Though not a "package" in name, this can be used wherever packages are
accepted.

### package(*name*, [*version*], [*lang*], [*kind*], [*headers*], [*libs*]) { #package }
Availability: `build.bfg`
{: .subtitle}

Search for a package named *name*. *lang* is the source language of the library
(`'c'` by default); this will affect how the package is resolved. For native
libraries (C, C++, Fortran, etc), this will use [`pkg-config`][pkg-config] to
resolve the package if it's installed. Otherwise (or if pkg-config can't find
the package), this will check the system's default library locations. If this
function is unable to find the package, it will raise a
[*PackageResolutionError*](#packageresolutionerror).

You can also specify *kind* to one of `'any'` (the default), `'shared'`, or
`'static'`. This allows you to restrict the search to find only static versions
of a library, for example.

If *version* is specified, it will (if possible) ensure that the installed
version of the package meets the version requirement; it must be formatted as a
Python [version specifier][version-specifier]. If this check fails, a
[*PackageVersionError*](#packageversionerror) will be raised.

The *headers* and *libs* arguments can be used as fallbacks when pkg-config
fails to resolve the package. *headers* allows you to specify a header file (or
list thereof) that you need to use in your source files. This will search for
the header files and add the appropriate include directories to your build
configuration. *libs* lets you list any library names that are part of this
package; by default, this is set to the package's *name*. You can also pass
*None* to *libs* in order to explicitly indicate that the library is
header-only.

This function recognizes the following environment variables:
[`CLASSPATH`](environment-vars.md#classpath),
[`CPATH`](environment-vars.md#cpath),
[`INCLUDE`](environment-vars.md#include),
[`LIB`](environment-vars.md#lib),
[`LIBRARY_PATH`](environment-vars.md#library_path),
[`PKG_CONFIG`](environment-vars.md#pkg_config).

!!! note
    This function can also be used to refer to the pthread library. On many
    Unix-like systems, instead of using `-lpthread` during the link step, it's
    preferred to use `-pthread` during compilation *and* linking. Using
    `package('pthread')` will handle this automatically.

### pkg_config([*name*], [*desc_name*], [*desc*], [*url*], [*version*], [*requires*], [*requires_private*], [*conflicts*], [*includes*], [*libs*], [*libs_private*], [*options*], [*link_options*], [*link_options_private*], [*auto_fill*]) { #pkg_config }
Availability: `build.bfg`
{: .subtitle}

Create [pkg-config][pkg-config] information for this project and install it
along with the rest of the installed files. All of these arguments are optional
and will be automatically inferred from the rest of the build where possible.
Unless otherwise noted, these arguments correspond directly to the fields in the
pkg-config `.pc` file.

* *name*: The name of the package (to be used at the name of the `.pc` file)
* *desc_name*: A human-readable name for the package (stored as the `Name`
  field in pkg-config); defaults to *name*
* *desc*: A brief description of the package; defaults to `<name> library`
* *url*: A URL where users can learn more about the package
* *version*: The package's version
* *requires*: A list of packages required by this package; these can be strings,
  a string and version specifier, or the results from [*package*](#package). In
  the last case, packages resolved by pkg-config are added directly as
  requirements; those resolved by other means are added to the `Libs` field in
  pkg-config
* *requires_private*: A list of packages required by this package but not
  exposed to users; these can be specified as with *requires*
* *conflicts*: A list of packages that conflict with this package; these can be
  specified as with *requires*
* *includes*: A list of [directories](#header_directory) (or [header
  files](#header_file)) to add to the search path for users of this package
* *libs*: A list of [libraries](#library) for users of this package to link to;
  any dependent libraries, packages, or link options (in the case of static
  libs) will automatically be added to *libs_private*, *requires_private*, and
  *link_options_private*, respectively
* *libs_private*: A list of [libraries](#library) required by this package but
  not exposed to users (this is used primarily for static linking); dependent
  libraries, packages, and link options are added as with *libs*
* *options*: A list of compile options for this package
* *link_options*: A list of link options for this package
* *link_options_private*: A list of link options for this package but not
  exposed to users (this is used primarily for static linking)
* *lang*: The language of the builder to use when generating option strings;
  by default, `'c'`

If *auto_fill* is true (the default), this function will automatically fill in
default values for the following fields:

* *name*: The [project's name](#project) (this also fills in *desc_name* and
  *desc* with default values)
* *version*: The [project's version](#project), or `0.0` if none is specified
* *includes*: The list of [installed](#install) header files/directories
* *libs*: The list of [installed](#install) library files

### system_executable(*name*) { #system_executable }
Availability: `build.bfg`
{: .subtitle}

Search for an executable named *name* somewhere in the system's PATH.

This function recognizes the following environment variables:
[`PATH`](environment-vars.md#path), [`PATHEXT`](environment-vars.md#pathext).

## Environment

Occasionally, build scripts need to directly query aspects of the environment.
In bfg9000, this is performed with the
[*environment object*](#environment-object) and its various members.

### Environment object

The *environment*, `env`, is a special object that encapsulates information
about the system outside of bfg9000. It's used internally for nearly all
platform-specific code, but it can also help in `build.bfg` (or `options.bfg`!)
files when you encounter some unavoidable issue with multiplatform
compatibility.

!!! note
    This listing doesn't cover *all* available functions on the environment,
    since many are only useful to internal code. However, the most relevant ones
    for `build.bfg` files are shown below.

#### env.builder(*lang*) { #env-builder }

Return the [builder](#builders) used by bfg9000 for a particular language
*lang*.

#### env.execute(*args*, [*env*], [*env_update*], [*shell*], [*stdout*], [*stderr*], [*returncode*]) { #env-execute }

Execute the command-line arguments in *args* and return the output. If *shell*
is true, *args* should be a string that will be interpreted by the system's
shell; if not (the default), it should be a series of arguments.

You can also set *env* to be a dictionary of environment variables to pass to
the child process. If *env_update* is true (the default), these will be added to
the environment variables in [*env.varables*](#env-variables); otherwise, *env*
represents *all* the environment variables to pass to the child process.

*stdout* and *stderr* are [*env.Mode*](#env-Mode) values that describe how (or
if) output should be redirected. By default, both are set to *Mode.normal*.

Finally, *returncode* specifies the expected return code from the subprocess.
This is 0 by default, and may be either a number, a list of numbers, or `'any'`
to match any return code. If the return code fails to match, a
[*CalledProcessError*](#CalledProcessError) will be thrown.

#### env.getvar(*name*, [*default*]) { #env-getvar }

Equivalent to *[env.variables](#env-variables).get(name, default)*.

#### env.host_platform { #env-host_platform }

Return the host [platform](#platforms) used for the build.

#### env.Mode { #env-Mode }

An enumeration of output modes for [*env.execute*](#env-execute) and
[*env.run*](#env-run). Possible values are:

* *normal*: Perform no redirection and output to stdout/stderr normally
* *pipe*: Pipe the output and return it to the calling process
* *stdout*: Pipe stderr output to stdout
* *devnull*: Pipe output to `/dev/null` or equivalent

#### env.run_arguments(*args*, [*lang*]) { #env-run_arguments }

Generate the arguments needed to run the command in *args*. If *args* is a file
type (or a list beginning with a file type) such as an
[*executable*](#executable), it will be prepended with the
[runner](#builder-runner) for *lang* as needed. If *lang* is *None*, the
language will be determined by the language of *args*'s first element.

#### env.run(*args*, [*lang*], [*env*], [*env_update*], [*stdout*], [*stderr*], [*returncode*]) { #env-run }

Run a command, generating any arguments needed to perform the operation.
Equivalent to `env.execute(env.run_arguments(arg, lang), ...)`.

#### env.target_platform { #env-host_platform }

Return the target [platform](#platforms) used for the build.

#### env.variables { #env-variables }

A dict of all the environment variables as they were defined when the build was
first configured.

---

### Builders

Builder objects represent the toolset used to build [executables](#executable)
and [libraries](#library) for a particular source language. They can be
retrieved via [*env.builder*](#env-builder). While builder objects are primarily
suited to bfg's internals, there are still a few useful properties for
`build.bfg` files:

#### *builder*.flavor { #builder-flavor }

The "flavor" of the builder, i.e. the kind of command-line interface it has.
Possible values are `'cc'`, `'msvc'`, and `'jvm'`.

#### *builder*.brand { #builder-brand }

The brand of the builder, i.e. the command name people use for it. Currently,
for languages in the C family (including Fortran), this is one of `'gcc'`,
`'clang'`, `'msvc'`, or `'unknown'`. For languages in the Java family, this is
one of `'oracle'`, `'openjdk'`, `'epfl'` (for Scala), or `'unknown'`.

#### *builder*.version { #builder-version }

The version of the builder (specifically, the version of the primary compiler
for the builder). May be *None* if bfg9000 was unable to detect the version.

#### *builder*.lang { #builder-lang }

The language of the source files that this builder is designed for.

#### *builder*.object_format { #builder-object_format }

The object format that the builder outputs, e.g. `'elf'`, `'coff'`, or `'jvm'`.

#### *builder*.compiler { #builder-compiler }

The [compiler](#compilers) used with this builder.

#### *builder*.pch_compiler { #builder-compiler }

The [compiler](#compilers) used to build precompiled headers with this builder.
May be *None* for languages or toolsets that don't support precompiled headers.

#### *builder*.linker(*mode*) { #builder-linker }

The linker used with this builder. *mode* is one of `'executable'`,
`'shared_library'`, or `'static_library'` Its public properties are the same as
[*compiler*](#compilers).

`cc`-like builders also support a *mode* of `'raw'`, which returns an object
representing the actual linker, such as `ld`.

#### *builder*.runner { #builder-runner }

The runner used with files built by this builder (e.g. `java`). This may be
*None* for languages which have no runner, such as C and C++.

---

### Compilers

Builder objects represent the specific used to compile a
[source file](#source_file) (generally into an [object file](#object_file)).

#### *compiler*.flavor { #compiler-flavor }

The "flavor" of the compiler, i.e. the kind of command-line interface it has;
e.g. `'cc'`, `'msvc'`.

#### *compiler*.brand { #compiler-brand }

The brand of the compiler; typically the same as
[*builder.brand*](#builder-brand).

#### *compiler*.version { #compiler-version }

The version of the compiler; typically the same as
[*builder.version*](#builder-version).

#### *compiler*.language { #compiler-language }

The language of the compiler; typically the same as
[*builder.language*](#builder-language).

#### *compiler*.command { #compiler-command }

The command to run when invoking this compiler, e.g. `g++-4.9`.

---

### Platforms

Platform objects represent the platform that the project is being compiled for.

#### *platform*.family { #platform-flavor }

The family of the platform. Either `'posix'` or `'windows'`.

#### *platform*.genus { #platform-genus }

The sub-type of the platform, e.g. `'linux'`, `darwin'`, or `'winnt'`.

#### *platform*.name { #platform-name }

An alias for [*platform.species*](#platform-species).

#### *platform*.species { #platform-species }

The specific name of the platform, e.g. `'linux'`, `'macos'`, or `'winnt'`.

## Utilities

### argument(*names*..., [*action*], [*nargs*], [*const*], [*default*], [*type*], [*choices*], [*required*], [*help*], [*metavar*], [*dest*]) { #argument }
Availability: `options.bfg`
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

### argv
Availability: `build.bfg`
{: .subtitle}

Retrieve the set of [user-defined arguments](writing.md#user-defined-arguments)
passed to bfg9000; this is an [*argparse.Namespace*][namespace] object.

### \__bfg9000__
Availability: `build.bfg`, `options.bfg`, and `<toolchain>.bfg`
{: .subtitle}

A dictionary containing all the builtin functions and global variables defined
by bfg9000. This can be useful for feature detection or accessing builtins
shadowed by a local variable.

### bfg9000_required_version([*version*], [*python_version*]) { #bfg9000_required_version }
Availability: `build.bfg`, `options.bfg`, and `<toolchain>.bfg`
{: .subtitle}

Set the required *version* for bfg9000 and/or the required *python_version*.
Each of these is a standard Python [version specifier][version-specifier]. If
the actual versions don't match the specifiers, a
[*VersionError*](#versionerror) is raised.

### bfg9000_version
Availability: `build.bfg`, `options.bfg`, and `<toolchain>.bfg`
{: .subtitle}

Return the current version of bfg9000. This can be useful if you want to
optionally support a feature only available in certain versions of bfg.

### debug(*message*, [*show_stack*]) { #debug }

Log a debug message with the value *message*. If *show_stack* is true (the
default), show the stack trace where the message was logged from.

!!! note
    Debug messages are hidden by default; pass `--debug` on the command line to
    them.

### filter_by_platform(*name*, *path*, *type*) { #filter_by_platform }
Availability: `build.bfg`
{: .subtitle}

Return *FindResult.include* if *path* is a filename that should be included for
the target platform, and *FindResult.not_now* otherwise. File (or directory)
names like `PLATFORM` or `foo_PLATFORM.cpp` are excluded if `PLATFORM` is a
known platform name that *doesn't* match the target platform. Known platform
names are: `'posix'`,`'linux'`, `'darwin'`, `'cygwin'`, `'windows'`, `'winnt'`,
`'win9x'`, `'msdos'`.

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

### info(*message*, [*show_stack*]) { #info }

Log an informational message with the value *message*. If *show_stack* is true,
show the stack trace where the message was logged from.

### project(*name*, [*version*]) { #project }
Availability: `build.bfg`
{: .subtitle}

Set the name (and optionally the version) of the project. If you don't call
this function to specify a project name, it defaults to the name of the
project's source directory. This is primarily useful for creating [source
distributions](writing.md#distributing-your-source).

### warning(*message*) { #warning }

Log a warning with the value *message* and the stack trace where the warning was
emitted.

## Toolchain

### compiler(*names*, *lang*) { #compiler }
Availability: `<toolchain>.bfg`
{: .subtitle}

Set the compiler to use for the language *lang*. *names* is a string
representing the path to the compiler (resolved as with [*which*](#which)) or a
list of possible paths (as strings or lists or strings). If *strict* is true,
*compiler* will raise an `IOError` if an executable cannot be found; if false,
it will use the first candidate.

### compile_options(*options*, *lang*) { #compile_options }
Availability: `<toolchain>.bfg`
{: .subtitle}

Set compilation options to use for the language *lang*. *options* is either a
string of all the options or a list of strings, one element per option.

!!! note
    [Semantic options](#semantic-options) aren't supported here; instead, you
    should use the appropriate option strings for the compiler to be used.

### environ
Availability: `<toolchain>.bfg`
{: .subtitle}

A `dict` of the current environment variables, suitable for getting/setting.

### install_dirs([...]) { #install_dirs }
Availability: `<toolchain>.bfg`
{: .subtitle}

Set the installation directories for this toolchain. Arguments to this function
should be keyword args with one of the following names: `prefix`, `exec_prefix`,
`bindir`, `libdir`, or `includedir`.

!!! note
    Any installation directory set here *overrides* directories set on the
    command line.

### lib_options(*options*, [*format*], [*mode*]) { #lib_options }
Availability: `<toolchain>.bfg`
{: .subtitle}

Set lib options to use for the format *format* (defaults to `'native'`) and
mode *mode* (defaults to `'dynamic'`). *options* is either a string of all the
options or a list of strings, one element per option. Unlike
[*link_options*](#link_options), this is used to specify options which appear at
the *end* of a linker command (like `$LDLIBS`).

### linker(*names*, [*format*], [*mode*]) { #linker }
Availability: `<toolchain>.bfg`
{: .subtitle}

Set the link to use for the format *format* (defaults to `'native'`) and mode
*mode* (defaults to `'dynamic'`). *names* is a string representing the path to
the linker (resolved as with [*which*](#which)) or a list of possible paths (as
strings or lists or strings). If *strict* is true, *linker* will raise an
`IOError` if an executable cannot be found; if false, it will use the first
candidate.

### link_options(*options*, [*format*], [*mode*]) { #link_options }
Availability: `<toolchain>.bfg`
{: .subtitle}

Set link options to use for the format *format* (defaults to `'native'`) and
mode *mode* (defaults to `'dynamic'`). *options* is either a string of all the
options or a list of strings, one element per option.

### runner(*names*, *lang*) { #runner }
Availability: `<toolchain>.bfg`
{: .subtitle}

Set the runner to use for the language *lang*, if that language supports runners
(e.g. Java, Scala, or a scripting language). *names* is a string representing
the path to the compiler (resolved as with [*which*](#which)) or a list of
possible paths (as strings or lists or strings). If *strict* is true,
*compiler* will raise an `IOError` if an executable cannot be found; if false,
it will use the first candidate.

### target_platform([*platform*], [*arch*]) { #target_platform }
Availability: `<toolchain>.bfg`
{: .subtitle}

Set the target platform of this build to *platform* and the architecture to
*arch*. If either is not specified, the host system's platform/arch will be
used.

The following platforms are recognized: `'android'`, `'cygwin'`, `'ios'`,
`'linux'`, `'macos'`, `'win9x'`, and `'winnt'`. Other platforms (e.g.
`'freebsd'`) can be specified, and will be treated as generic POSIX platforms.

### which(*names*, [*resolve*], [*strict*]) { #which }
Availability: `<toolchain>.bfg`
{: .subtitle}

Find the best option for an executable named by *names*. *names* can be a
string resolved as with the `PATH` environment variable in the shell, or else a
list of names (as strings or lists of strings). If *names* contains a
list-of-lists, the inner list represents a series of arguments to pass to the
executable when running it.

If *strict* is true (the default), *which* will raise an `IOError` if an
executable cannot be found; if false, it will return the first candidate as a
string.

## Exceptions

### CalledProcessError
Availability: `build.bfg` and `options.bfg`
{: .subtitle}

An exception raised when a subprocess fails to execute successfully. This is
just an alias for the standard Python error
[*subprocess.CalledProcessError*][subprocess-CalledProcessError].

### PackageResolutionError
Availability: `build.bfg` and `options.bfg`
{: .subtitle}

An exception raised when a [package resolution function](#package-resolvers) is
unable to find the specified package.

### PackageVersionError
Availability: `build.bfg` and `options.bfg`
{: .subtitle}

An exception raised when a [package resolution function](#package-resolvers)
found the specified package, but its version doesn't match the version
specifier. Derived from both
[*PackageResolutionError*](#packageresolutionerror) and
[*VersionError*](#versionerror).

### VersionError
Availability: `build.bfg` and `options.bfg`
{: .subtitle}

An exception raised when a version fails to match the supplied version
specifier.

[system-directory]: https://gcc.gnu.org/onlinedocs/cpp/System-Headers.html
[def-file]: https://docs.microsoft.com/en-us/cpp/build/reference/module-definition-dot-def-files
[gcc-pch]: https://gcc.gnu.org/onlinedocs/gcc/Precompiled-Headers.html
[clang-pch]: http://clang.llvm.org/docs/UsersManual.html#usersmanual-precompiled-headers
[msvc-pch]: https://msdn.microsoft.com/en-us/library/szfdksca.aspx
[whole-archive]: http://linux.die.net/man/1/ld
[boost]: https://www.boost.org/
[version-specifier]: https://www.python.org/dev/peps/pep-0440/#version-specifiers
[framework]: https://developer.apple.com/library/content/documentation/MacOSX/Conceptual/OSX_Technology_Overview/SystemFrameworks/SystemFrameworks.html
[pkg-config]: https://www.freedesktop.org/wiki/Software/pkg-config/
[add_argument]: https://docs.python.org/library/argparse.html#the-add-argument-method
[namespace]: https://docs.python.org/library/argparse.html#argparse.Namespace
[subprocess-CalledProcessError]: https://docs.python.org/library/subprocess.html#subprocess.CalledProcessError
