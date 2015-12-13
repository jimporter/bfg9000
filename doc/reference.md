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

### object_files(*files*[, *include*], [*packages*], [*options*], [*lang*], [*extra_deps*])

### shared_library(*name*[, *files*, [*include*], [*libs*], [*packages*], [*compile_options*], [*link_options*], [*lang*], [*extra_deps*]])

### static_library(*name*[, *files*, [*include*], [*libs*], [*packages*], [*compile_options*], [*link_options*], [*lang*], [*extra_deps*]])

## Other rules

### default(*...*)

### global_options(*options*, *lang*)

### global_link_options(*options*)

### install(*...*, [*all*])

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
