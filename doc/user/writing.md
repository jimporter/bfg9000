# Writing a Build File

bfg9000's build script is called `build.bfg` and is (usually) placed in the root
of your source tree. `build.bfg` files are just Python scripts with a handful of
extra built-in functions to define all the rules for building your software.
While bfg9000's goal is to make writing build scripts easy, sometimes complexity
is unavoidable. By using a general-purpose language, this complexity can
(hopefully!) be managed.

## Your first build script

The simplest build script, compiling a single source file into an
[executable](reference.md#executablename-files-extra_deps), is indeed very
simple:

```python
executable('simple', files=['simple.cpp'])
```

The above is all you need to build your executable for any supported build
backend and platform. The output file's name is automatically converted to the
appropriate name for the target platform (`'simple'` on Linux and OS X and
`'simple.exe'` on Windows).

## Building executables

We've already seen how to build simple executables, but build tools aren't much
good if that's all they can do! Naturally, it's easy to build an executable from
multiple source files (just add more elements to the *files* argument), but
there are plenty of other things you'd probably like to do with your build
scripts.

### Implicit conversions

bfg9000 tries its best to make your build scripts easy to read and to minimize
verbosity. First, arguments that normally take a list can take a single item
instead, e.g. `executable('simple', files='simple.cpp')`. In addition, bfg9000
will automatically convert a string argument to an object of the appropriate
type. In the previous example, `'simple.cpp'` is automatically converted to a
[*source_file*](reference.md#source_filename-lang).

### Sudirectories

Many projects organize their headers and source files into different
directories. For source files, this is easy to handle: just write out the
relative path to the file. For header files, you need to let your compiler know
where they're located. The
[*header_directory*](reference.md#header_directoryname-system) function creates
a reference to the directory, which can then be passed to your build function
via the *include* argument:

```python
include_dir = header_directory('include')
executable('program', files=['src/prog.cpp'], include=[include_dir])
```

As noted above, you can also simplify this to:

```python
executable('program', files='src/prog.cpp', include='include')
```

Of course, bfg9000 also allows you to place built files in subdirectories as
well. Simply specify the relative path as the name of executable (or whatever
type of file you're building).

### Options

Build scripts often need to set options when compiling/linking binaries.
Sometimes, these are specific to a single executable in the project, and other
times they apply to *all* the binaries. bfg9000 supports both cases. You can
provide options for a single binary with the *compile_options* and
*link_options* arguments:

```python
executable('simple', files=['simple.cpp'], compile_options=['-Wall', '-Werror'],
           link_options=['-static-libstdc++'])
```

You can also specify [global compiler
options](reference.md#global_optionsoptions-lang) (on a per-language basis) as
well as [global linker options](reference.md#global_link_optionsoptions):

```python
global_options(['-Wall', '-Werror'], lang='c++')
global_link_options(['-static-libstdc++'])
```

Naturally, the interpretations of these arguments depend on the compiler being
used, so it's important to be sure the compiler understands the arguments. You
can determine the kind of compiler being used by consulting the build's
[Environment](reference.md#environment) and checking the compiler's
[*flavor*](reference.md#compilerflavor).

## Building libraries

## Default build

## External packages

## Installation

## Commands

## Tests

## Finding files
