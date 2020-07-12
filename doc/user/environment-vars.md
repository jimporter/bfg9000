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
cc-style toolchains when linking object files whose source is in C. If not
defined, bfg9000 will try to guess the command to use by checking
[`OBJC`](#objc), [`CXX`](#cxx), and [`OBJCXX`](#objcxx), in that order.

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
cc-style toolchains when linking object files whose source is in C++. If not
defined, bfg9000 will try to guess the command to use by checking
[`OBJCXX`](#objcxx), [`CC`](#cc), and [`OBJC`](#objc), in that order.

#### *CXXFLAGS*
Default: *none*
{: .subtitle}

Command line arguments to pass to the compiler when compiling any C++ source
file.

### Fortran
---

#### *FC*
Default: `gfortran`
{: .subtitle}

The command to use when compiling Fortran source files. Also the command to use
when linking object files whose source is in Fortran.

#### *FFLAGS*
Default: *none*
{: .subtitle}

Command line arguments to pass to the compiler when compiling any Fortran source
file.

### Java
---

#### *JAVAC*
Default: `javac`
{: .subtitle}

The command to use when compiling Java source files.

#### *JAVAFLAGS*
Default: *none*
{: .subtitle}

Command line arguments to pass to the compiler when compiling any Java source
file.

### Lex
---

#### *LEX*
Default: `lex`
{: .subtitle}

The command to use when building Lex source files.

#### *LFLAGS*
Default: *none*
{: .subtitle}

Command line arguments to pass to the compiler when building any Lex source
file.

### Objective C
---

#### *OBJC*
Default: `cc`
{: .subtitle}

The command to use when compiling Objective C source files. Also the command to
use with cc-style toolchains when linking object files whose source is in
Objective C. If not defined, bfg9000 will try to guess the command to use by
checking [`CC`](#cc), [`OBJCXX`](#objcxx), and [`CXX`](#cxx), in that order.

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
Objective C++. If not defined, bfg9000 will try to guess the command to use by
checking [`CXX`](#cxx), [`OBJC`](#objc), and [`CC`](#cc), in that order.

#### *OBJCXXFLAGS*
Default: *none*
{: .subtitle}

Command line arguments to pass to the compiler when compiling any Objective C++
source file.

### Qt MOC
---

#### *MOC*
Default: `moc`
{: .subtitle}

The command to use when processing Qt meta-object macros.

#### *MOCFLAGS*
Default: *none*
{: .subtitle}

Command line arguments to pass to the compiler when processing Qt meta-object
macros.

### Qt QRC
---

#### *RCC*
Default: `rcc`
{: .subtitle}

The command to use when building Qt `.qrc` files.

#### *RCCFLAGS*
Default: *none*
{: .subtitle}

Command line arguments to pass to the compiler when building Qt `.qrc` files.

### Qt UI
---

#### *UIC*
Default: `uic`
{: .subtitle}

The command to use when building Qt `.ui` files.

#### *UICFLAGS*
Default: *none*
{: .subtitle}

Command line arguments to pass to the compiler when building Qt `.ui` files.
macros.

### Scala
---

#### *SCALAC*
Default: `scalac`
{: .subtitle}

The command to use when compiling Scala source files.

#### *SCALAFLAGS*
Default: *none*
{: .subtitle}

Command line arguments to pass to the compiler when compiling any Scala source
file.

### Yacc
---

#### *YACC*
Default: `yacc`
{: .subtitle}

The command to use when building Yacc source files.

#### *YFLAGS*
Default: *none*
{: .subtitle}

Command line arguments to pass to the compiler when building any Yacc source
file.

## Linking variables

### Static linking
---

#### *AR*
Default: `ar` (POSIX), `lib` (Windows)
{: .subtitle}

The command to use when creating (native) static libraries from object files
(typically `ar` on POSIX and `lib` on Windows).

#### *ARFLAGS*
Default: `cru` (POSIX)
{: .subtitle}

The arguments to pass to the static library builder (specified in `AR`) for
native libraries.

#### *JAR*
Default: `jar`
{: .subtitle}

The command to use when creating `.jar` files for JVM-based binaries.

#### *JARFLAGS*
Default: `cfm`
{: .subtitle}

The arugments to pass to the JAR builders when creating `.jar` files.

### Dynamic linking
---

#### *LD*
Default: *none* (POSIX), `link` (Windows)
{: .subtitle}

The command to use when linking shared libraries; when using a cc-like builder,
this will be processed to infer the appropriate `-fuse-ld` flag for the linker.

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

## Execution variables
---

#### *JAVACMD*
Default: `java`
{: .subtitle}

The command to use when running Java `.class` files or `.jar`s. (Does not apply
when building with GCJ.)

#### *LUA*
Default: `lua`
{: .subtitle}

The command to use when running Lua scripts.

#### *PERL*
Default: `perl`
{: .subtitle}

The command to use when running Perl scripts.

#### *PYTHON*
Default: *sys.executable*
{: .subtitle}

The command to use when running Python scripts. By default, this is the
interpreter used to run bfg9000.

#### *RUBY*
Default: `ruby`
{: .subtitle}

The command to use when running Ruby scripts.

#### *SCALACMD*
Default: `scala`
{: .subtitle}

The command to use when running Scala `.class` files or `.jar`s.

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

#### *CLASSPATH*
Default: *none*
{: .subtitle}

A list of additional directories to search for Java class files. On POSIX
systems, this is delimited by `:`; on Windows, by `;`.

#### *CPATH*
Default: *none*
{: .subtitle}

A list of additional directories to search for headers. On POSIX systems, this
is delimited by `:`; on Windows, by `;`.

#### *INCLUDE*
Default: *none*
{: .subtitle}

*MSVC-only*. A list of directories to search for headers, delimited by `;`.

#### *LIB*
Default: *none*
{: .subtitle}

*MSVC-only*. A list of directories to search for [system
libraries](reference.md#package), delimited by `;`.

#### *LIBRARY_PATH*
Default: *none*
{: .subtitle}

A list of additional directories to search for [system
libraries](reference.md#package). On POSIX systems, this is delimited by
`:`; on Windows, by `;`.

#### *PATH*
Default: *none*
{: .subtitle}

A list of directories to search for [system
executables](reference.md#system_executable). On POSIX systems, this is
delimited by `:`; on Windows, by `;`.

#### *PATHEXT*
Default: *none*
{: .subtitle}

*Windows-only*. A list of valid extensions for executable files under Windows,
separated by `;`.

#### *PKG_CONFIG*
Default: `pkg-config`
{: .subtitle}

The command to use when fetching pkg-config package information.

## Command variables
---

#### *BFG9000*
Default: `/path/to/bfg9000`
{: .subtitle}

The command to use when executing bfg9000 (e.g. when regenerating the build
scripts because the list of source files has changed). This should only be
necessary if you run bfg9000 from a wrapper script.

#### *CP*
Default: `cp -f` (POSIX), `cmd /c copy` (Windows)
{: .subtitle}

The command to use when creating symlinks.

#### *DEPFIXER*
Default: `/path/to/bfg9000-depfixer`
{: .subtitle}

The command to use when fixing up depfiles generated by your compiler for the
Make backend. In general, you shouldn't need to touch this.

#### *DOPPEL*
Default: `doppel`
{: .subtitle}

The command to use when installing files and building source distributions. For
more information about doppel, see its [documentation][doppel].

#### *HARDLINK*
Default: `ln -f` (POSIX), `cmd /c mklink /H` (Windows)
{: .subtitle}

The command to use when creating hard links.

#### *INSTALL_NAME_TOOL*
Default: `install_name_tool`
{: .subtitle}

*Darwin-only*. The command to use when modifying the paths of the shared
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

#### *RCCDEP*
Default: `/path/to/bfg9000-rccdep`
{: .subtitle}

The command to use when generating depfiles for Qt's `rcc` tool. In general, you
shouldn't need to touch this.

#### *SETENV*
Default: `/path/to/bfg9000-setenv`
{: .subtitle}

*Windows-only*. The command to use when setting temporary environment variables,
similar to the POSIX `env` command. This is used when setting environment
variables for tests.

#### *SYMLINK*
Default: `ln -sf` (POSIX), `cmd /c mklink` (Windows)
{: .subtitle}

The command to use when creating symlinks.

## System variables
---

#### *DESTDIR*
Default: *none*
{: .subtitle}

*POSIX-only*. A directory to prepend to the install location for the project,
used in performing staged installs. For more information, see the [GNU coding
standards][destdir].

#### *PLATFORM*
Default: `Win32`
{: .subtitle}

*Windows-only*. The platform type to use when generating MSBuild files.

#### *VISUALSTUDIOVERSION*
Default: `14.0`
{: .subtitle}

*Windows-only*. The version of Visual Studio to target when generating MSBuild
files.

[doppel]: https://github.com/jimporter/doppel
[destdir]: https://www.gnu.org/prep/standards/html_node/DESTDIR.html
