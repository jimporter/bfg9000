# Reference

## File types

### header(*name*)

### header_directory(*directory*)

### source_file(*name*[, *lang*])

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

### executable(*name*, [*files*, [*include*], [*libs*], [*packages*], [*compile_options*], [*link_options*], [*lang*], [*extra_deps*]])

Create a build step that builds an executable file named *name*. *files* is the
list of source (or object) files to link. Library files can be specified in
*libs*, while libraries from external packages can be specified in *packages*
(see [Package finders](#package-finders) below). You can also pass command-line
options for the linker in *link_options*. The arguments *include*,
*compile_options*, *packages*, and *lang* are all forwarded on to the
*object_file()* step (with *compile_options* mapping to *options*) for any
source files listed in *files*.

If *files* isn't specified, this function merely references an *existing*
executable file (a precompiled binary, a shell script, etc) somewhere on the
filesystem. In this case, *name* is the exact name of the file. This allows
you to refer to existing executables for other functions.

### object_file([*name*], [*file*, [*include*], [*packages*], [*options*], [*lang*], [*extra_deps*]])

Create a build step that compiles a source file named *file* to an object file
named *name*; if *name* is not specified, it takes the file name in *file*
without the extension. You can specify directories to search for header files in
*include* (see [header_directory](#header_directorydirectory)), while external
[packages](#package-finders) can be specified in *packages*. Command-line
compiler options may be specified in *options*. *lang* can be used to specify
the source language for the executable; this is useful if the source file's
extension isn't recognized by bfg9000.

If *file* isn't specified, this function merely references an *existing*
object file somewhere on the filesystem. In this case, *name* must be specified
and is the exact name of the file.

### object_files(*files*[, *include*], [*packages*], [*options*], [*lang*], [*extra_deps*])

Create a compilation build step for each of the files in *files*; this is
equivalent to calling
[object_file](object_filename-file-include-packages-options-lang-extra_deps)
for each element in *files*.

### shared_library(*name*[, *files*, [*include*], [*libs*], [*packages*], [*compile_options*], [*link_options*], [*lang*], [*extra_deps*]])

Create a build step that builds a shared library named *name*. Its arguments are
the same as [executable](#executablename-files-include-libs-packages-compile_options-link_options-lang-extra_deps).

!!! note
    On Windows, this produces *two* files: `name.dll` and `name.lib`. The latter
    is the *import library*, used when linking to this library. As a result,
    `my_lib.all` returns a list containing two files.

### static_library(*name*[, *files*, [*include*], [*libs*], [*packages*], [*compile_options*], [*link_options*], [*lang*], [*extra_deps*]])

Create a build step that builds a static library named *name*. Its arguments are
the same as [executable](#executablename-files-include-libs-packages-compile_options-link_options-lang-extra_deps).

## Other rules

### default(*...*)

Specify a list of build steps that should be run by default when building. These
are all accumulated into the `"all"` target.

### global_options(*options*, *lang*)

### global_link_options(*options*)

### install(*...*, [*all*])

Specify a list of files that need to be installed for the project to work. Each
will be installed to the appropriate location based on its type (e.g. header
files will go in `$PREFIX/include` by default on POSIX systems).

If *all* is `True`, all the files will be installed; otherwise, only the primary
file for each argument will be. For instance, on Windows, this means that
setting *all* to `True` installs the import libraries as well as the DLLs for
shared libraries.

### test(*test*, [*options*], [*environment*], [*driver*])

### test_driver(*driver*, [*options*], [*environment*], [*parent*])

### test_deps(*...*)

## Package finders

### boost_package([*name*], [*version*])

### system_executable(*name*)

### system_package(*name*)

## Miscellaneous

### bfg9000_required_version([*version*], [*python_version*])

### filter_by_platform(*name*, *type*)

### find_files([*path*], [*name*], [*type*], [*flat*], [*filter*], [*cache*])
