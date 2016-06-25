# Writing a Build File

bfg9000's build script is called `build.bfg` and is (usually) placed in the root
of your source tree. `build.bfg` files are just Python scripts with a handful of
extra built-in functions to define all the rules for building your software.
While bfg9000's goal is to make writing build scripts easy, sometimes complexity
is unavoidable. By using a general-purpose language, this complexity can
(hopefully!) be managed.

## Your first build script

The simplest build script, compiling a single source file into an
[executable](reference.md#executable), is indeed very simple:

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
[*source_file*](reference.md#source_file).

### Sudirectories

Many projects organize their headers and source files into different
directories. For source files, this is easy to handle: just write out the
relative path to the file. For header files, you need to let your compiler know
where they're located. The
[*header_directory*](reference.md#header_directory) function creates
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

You can also specify [global compiler options](reference.md#global_options) (on
a per-language basis) as well as [global linker
options](reference.md#global_link_options):

```python
global_options(['-Wall', '-Werror'], lang='c++')
global_link_options(['-static-libstdc++'])
```

Naturally, the interpretations of these arguments depend on the compiler being
used, so it's important to be sure the compiler understands the arguments. You
can determine the kind of compiler being used by consulting the build's
[Environment](reference.md#environment) and checking the compiler's
[*flavor*](reference.md#compiler-flavor).

## Building libraries

Similar to building executables, you can also build
[shared](reference.md#shared_library) and [static](reference.md#static_library)
libraries. These take the same arguments as above, although static libraries
have no use for the *link_options* argument.

Once you've defined rules to build a library, you can pass it along to an
executable or other shared library via the *libs* argument:

```python
shared = shared_library('shared', files=['shared.cpp'])
static = static_library('shared', files=['static.cpp'])
executable('program', files=['program.cpp'], libs=[shared, static])
```

### Building libraries on Windows

On Windows, native shared libraries need to annotate public symbols so that the
dynamic linker knows what to do. To facilitate this, bfg9000 automatically
defines a preprocessor macro named for native-runtime languages (e.g. C or C++)
when building on Windows. For shared libraries, it defines `LIB<NAME>_EXPORTS`;
for static, `LIB<NAME>_STATIC`. The following snippet shows how you can use
these macros to set the appropriate attributes for your public symbols:

```c
#if defined(_WIN32) && !defined(LIBLIBRARY_STATIC)
#  ifdef LIBLIBRARY_EXPORTS
#    define LIB_PUBLIC __declspec(dllexport)
#  else
#    define LIB_PUBLIC __declspec(dllimport)
#  endif
#else
#  define LIB_PUBLIC
#endif
```

## Finding files

For projects with many source files, it can be inconvenient to manually list all
of them. Since `build.bfg` files are just Python scripts, you *could* use
Python's standard library to examine the file system and build the list.
However, there's a better way: bfg9000 provides a
[*find_files()*](reference.md#find_files) function to fetch the list; if the
list ever changes, the build files will be regenerated *automatically* the next
time they're run.

*find_files()* starts at a base directory and searches recursively for any files
matching a particular glob:

```python
hello_files = find_files('src/hello', '*.cpp')
executable('hello', files=hello_files)
```

There are lots of options you can pass to *find_files()* to tweak its behavior.
For instance, you can search only for files or only for directories by passing
`'f'` or `'d'`, respectively to the *type* argument.

## Default targets

When you're building multiple binaries, you might want to be able to specify
what gets built by default, i.e. when calling `make` (or `ninja`) with no
arguments. Normally, every executable and library (except those passed to
[*test()*](reference.md#test)) will get built. However, you can pass any build
rule(s) to [*default()*](reference.md#default), and they'll be set as the
default, overriding the normal behavior. This makes it easy to provide your
users with a standard build that gets them all the bits they need, and none they
don't.

## External packages

Most projects have external packages that they depend on. There are lots of
different ways these packages are organized, and bfg9000 currently supports
three of them: ["system" packages](reference.md#system_package) (libraries
installed into the default location for your system), [pkg-config
packages](reference.md#pkgconfig_package), and [Boost
packages](reference.md#boost_package):

```python
ogg = system_package('ogg', kind='static')
zlib = pkgconfig_package('zlib', version='>=1.2.8')
prog_opts = boost_package('program_options', version='>=1.55')
```

Each of these returns an object representing the package that can be used when
building binaries by passing them in the *packages* argument:

```python
executable('program', files=['main.cpp'], packages=[ogg, zlib, prog_opts])
```

## Installation

After building, you might want to allow your project to be installed onto the
user's system somewhere. Most files (headers, executables, libraries) can be
added to the list of installed files via the
[*install()*](reference.md#install) rule. You can also install entire
directories of headers:

```python
include_dir = header_directory('include')
lib = static_library('program', files=['src/prog.cpp'], include=[include_dir])
install(lib, include_dir)
```

## Commands

In addition to ordinary build rules, it can be useful to provide other common
commands that apply to a project's source, such as linting the code or building
documentation. Normally, you should pass the command to be run as an array of
arguments. This will automatically handle escaping any quotes in each argument.
This is especially important for cross-platform compatibility, since different
shells have different quoting rules:

```python
command('hello', cmd=['python', '-c', 'print("hello")'])
```

Of course, if you need to use your shell's special characters (like `&&`), you
can simply pass a string to the *cmd* argument. In addition, you can supply
multiple commands to this function via the *cmds* argument:

```python
command('script', cmds=[
    'touch file',
    ['python', 'script.py']
])
```

## Aliases

Sometimes, you just want to group a set of targets together to make it easier to
build all of them at once. This automatically happens for [default
targets](#default-targets) by creating an `all` alias, but you can do this
yourself for any collection of targets:

```python
foo = executable('foo', files=['foo.cpp'])
bar = executable('bar', files=['bar.cpp'])
alias('foobar', [foo, bar])
```

## Tests

All good projects should have tests. Since your project is good (isn't it?),
yours has tests too, and you should have a good way to execute those tests from
your build system. bfg9000 provides a [set of
functions](reference.md#test-rules) for running tests. The most important of
these is aptly named [*test()*](reference.md#test). Any executable can be passed
to this function, and it will be executed as a test; an exit status of 0 marks
success, and non-zero marks failure:

```python
test( executable('test_foo', files=['test_foo.cpp']) )
```

In addition, you can provide a [test driver](reference.md#test_driver) that
collects all of your tests together and runs them as one. *test_driver()* takes
an executable (a [*system_executable*](reference.md#system_executable) by
default) that runs all the test files. This allows you to aggregate multiple
test files into a single run, which is very useful for reporting:

```python
mettle = test_driver('mettle')
test( executable('test_foo', files=['test_foo.cpp']), driver=mettle )
test( executable('test_bar', files=['test_bar.cpp']), driver=mettle )
```
