# Environment Variables

bfg9000 reads from a number of environment variables. These are the primary way
in which users can customize parts of a specific build, e.g. by changing the
tools to use or adding compiler flags. Below is a full list of all the
environment variables bfg9000 recognizes.

## Compilation variables

### Generic
---

#### *CPPFLAGS*
Default: *none*
{: .subtitle}

"C preprocessor flags"; command line arguments to pass to the compiler when
compiling any C-family source file (C, C++, Objective C/C++).

### C
---

#### *CC*
Default: `cc` (POSIX), `cl` (Windows)
{: .subtitle}

The command to use when compiling C source files. Also the command to use with
cc-style toolchains when linking object files whose source is in C.

#### *CFLAGS*
Default: *none*
{: .subtitle}

Command line arguments to pass to the compiler when compiling any C source file.

### C++
---

#### *CXX*
Default: `c++` (POSIX), `cl` (Windows)
{: .subtitle}

The command to use when compiling C++ source files. Also the command to use with
cc-style toolchains when linking object files whose source is in C++.

#### *CXXFLAGS*
Default: *none*
{: .subtitle}

Command line arguments to pass to the compiler when compiling any C++ source
file.

### Objective C
---

#### *OBJC*
Default: `cc`
{: .subtitle}

The command to use when compiling Objective C source files. Also the command to
use with cc-style toolchains when linking object files whose source is in
Objective C.

#### *OBJCFLAGS*
Default: *none*
{: .subtitle}

Command line arguments to pass to the compiler when compiling any Objective C
source file.

### Objective C++
---

#### *OBJCXX*
Default: `c++`
{: .subtitle}

The command to use when compiling Objective C++ source files. Also the command
to use with cc-style toolchains when linking object files whose source is in
Objective C++.

#### *OBJCXXFLAGS*
Default: *none*
{: .subtitle}

Command line arguments to pass to the compiler when compiling any Objective C++
source file.

## Linking variables

### Static linking
---

#### *AR*
Default: `ar`
{: .subtitle}

*POSIX-only*. The command to use when creating static libraries from object
files.

#### *ARFLAGS*
Default: `cru`
{: .subtitle}

*POSIX-only*. The arguments to pass to the static library builder (typically
`ar`).

#### *CC_LIB*
Default: `lib`
{: .subtitle}

*MSVC-only*. The command to use when creating static libraries whose source
is in C.

#### *CXX_LIB*
Default: `lib`
{: .subtitle}

*MSVC-only*. The command to use when creating static libraries whose source
is in C++.

#### *LIBFLAGS*
Default: *none*
{: .subtitle}

*Windows-only*. Command line arguments to pass to the static library builder
(typically `lib`).

### Dynamic linking
---

#### *CC_LINK*
Default: `link`
{: .subtitle}

*MSVC-only*. The command to use when linking shared libraries whose source
is in C.

#### *CXX_LINK*
Default: `link`
{: .subtitle}

*MSVC-only*. The command to use when linking shared libraries whose source
is in C++.

#### *LDFLAGS*
Default: *none*
{: .subtitle}

Command line arguments to pass to the linker when linking an executable or
shared library.

#### *LDLIBS*
Default: *none*
{: .subtitle}

Additional libraries to link into an executable or shared library. This is
mainly useful for cases where a system library (e.g. the C++ Standard Library
implementation) requires another library to be explicitly linked with it.

## Packaging variables
---

#### *BOOST_ROOT*
Default: *none*
{: .subtitle}

The root directory where Boost headers and libraries are stored (as
`$BOOST_ROOT/include` and `$BOOST_ROOT/lib`, respectively).

#### *BOOST_INCLUDEDIR*
Default: *none*
{: .subtitle}

The root directory where Boost headers are stored. This takes precedence over
[*BOOST_ROOT*](#boost_root).

#### *BOOST_LIBRARYDIR*
Default: *none*
{: .subtitle}

The root directory where Boost libraries are stored. This takes precedence over
[*BOOST_ROOT*](#boost_root).

#### *CPATH*
Default: *none*
{: .subtitle}

A list of additional directories to search for headers. On POSIX systems, this
is delimited by `:`; on Windows, by `;`.

#### *INCLUDE*
Default: *none*
{: .subtitle}

*MSVC-only* A list of directories to search for headers, delimited by  `;`.

#### *LIB*
Default: *none*
{: .subtitle}

*MSVC-only* A list of directories to search for [system
libraries](reference.md#system_packagename), delimited by  `;`.

#### *LIBRARY_PATH*
Default: *none*
{: .subtitle}

A list of additional directories to search for [system
libraries](reference.md#system_packagename). On POSIX systems, this is delimited
by `:`; on Windows, by `;`.

#### *PATH*
Default: *none*
{: .subtitle}

A list of directories to search for [system
executables](reference.md#system_executablename). On POSIX systems, this is
delimited by `:`; on Windows, by `;`.

#### *PATHEXT*
Default: *none*
{: .subtitle}

*Windows-only*. A list of valid extensions for executable files under Windows,
separated by `;`.

## Command variables
---

#### *BFG9000*
Default: `/path/to/bfg9000`
{: .subtitle}

The command to use when executing bfg9000 (e.g. when regenerating the build
scripts because the list of source files has changed). This should only be
necessary if you run bfg9000 from a wrapper script.

#### *DEPFIXER*
Default: `/path/to/bfg9000-depfixer`
{: .subtitle}

The command to use when fixing up depfiles generated by your compiler for the
Make backend. In general, you shouldn't need to touch this.

#### *INSTALL*
Default: `install` (Linux, Windows), `ginstall` (Darwin)
{: .subtitle}

The command to use when installing files.

#### *INSTALL_NAME_TOOL*
Default: `install_name_tool`
{: .subtitle}

*Darwin-only* The command to use when modifying the paths of the shared
libraries linked to during installation.

#### *MKDIR_P*
Default: `mkdir -p`
{: .subtitle}

The command to use when making a directory tree. This is used both for
installing whole directories of files and for creating build directories under
the Make backend.

#### *PATCHELF*
Default: `patchelf`
{: .subtitle}

*Linux-only*. The command to use when patching an ELF file's rpath for
installation.

#### *SETENV*
Default: `/path/to/bfg9000-setenv`
{: .subtitle}

*Windows-only*. The command to use when setting temporary environment variables,
similar to the POSIX `env` command. This is used when setting environment
variables for tests.

## System variables
---

#### *PLATFORM*
Default: `Win32`
{: .subtitle}

*Windows-only*. The platform type to use when generating MSBuild files.

#### *VISUALSTUDIOVERSION*
Default: `14.0`
{: .subtitle}

*Windows-only*. The version of Visual Studio to target when generating MSBuild
files.
