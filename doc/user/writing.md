# Writing a Build File

bfg9000's build script is called `build.bfg` and is (usually) placed in the root
of your source tree. `build.bfg` files are just Python scripts with a handful of
extra built-in functions to define all the steps for building your software.
While bfg9000's goal is to make writing build scripts easy, sometimes complexity
is unavoidable. By using a general-purpose language, this complexity can
(hopefully!) be managed.

## Your first build script

The simplest build script, compiling a single source file into an
[executable](../reference/builtins.md#executable), is indeed very simple:

```python
executable('simple', files=['simple.cpp'])
```

The above is all you need to build your executable for any supported build
backend and platform. The output file's name is automatically converted to the
appropriate name for the target platform (`'simple'` on Linux and OS X and
`'simple.exe'` on Windows).

### Logging messages

Sometimes, it can be helpful to display messages to the user when they're
building your project. While `print`, `sys.stdout`, and the like work, these
aren't integrated into bfg9000's logging system. Instead, you can use
[*info()*](../reference/builtins.md#info),
[*warning()*](../reference/builtins.md#warning), or
[*debug()*](../reference/builtins.md#debug) to log your messages:

```python
try:
    pkg = package('optional_dependency')
except PackageResolutionError:
    warning('optional_dependency not found; fancy-feature disabled')
```

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
type. In the previous example, `'simple.cpp'` is automatically passed to
[*object_files*](../reference/builtins.md#object_files), which in turn converts
it to a [*source_file*](../reference/builtins.md#source_file) and generates the
appropriate build step.

### Subdirectories

Many projects organize their headers and source files into different
directories. For source files, this is easy to handle: just write out the
relative path to the file. For header files, you need to let your compiler know
where they're located. The
[*header_directory*](../reference/builtins.md#header_directory) function creates
a reference to the directory, which can then be passed to your build function
via the *include* argument:

```python
include_dir = header_directory('include')
executable('program', files=['src/prog.cpp'], includes=[include_dir])
```

As noted above, you can also simplify this to:

```python
executable('program', files='src/prog.cpp', includes='include')
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
options](../reference/builtins.md#global_options) (on a per-language basis) as
well as [global linker options](../reference/builtins.md#global_link_options):

```python
global_options(['-Wall', '-Werror'], lang='c++')
global_link_options(['-static-libstdc++'])
```

In addition to passing options as lists as above, you can also pass them as a
single string, which will be split according to the rules for sh-style command
line arguments.

#### Semantic options

Naturally, the interpretations of these options depend on the compiler (or
linker!) being used. One method is simply to the kind of compiler being used and
supply the appropriate option strings. You can do this by consulting the build's
[Environment](../reference/builtins.md#environment) and checking the compiler's
[*flavor*](../reference/builtins.md#compiler-flavor).

However, it's often better to use [*semantic
options*](../reference/builtins.md#semantic-options), options that are defined
as objects which will automatically be interpreted by the compiler:

```python
executable('simple', files=['simple.cpp'],
           compile_options=[opts.define('DEBUG')])
```

## Building libraries

In addition to building executables, you can obviously also build
[libraries](../reference/builtins.md#library). This takes the same arguments as
an executable as described above. Once you've defined how to build your library,
you can pass it along to an executable or other shared library via the *libs*
argument:

```python
lib = library('library', files=['library.cpp'])
executable('program', files=['program.cpp'], libs=[lib])
```

By default, this will create a shared library; however, when running bfg9000,
users can specify what kind of library to build by passing
`--enable-shared`/`--disable-shared` and `--enable-static`/`--disable-static` on
the command line.

When creating a static library, the `link_options` argument behaves specially:
it represents arguments that will be *forwarded* to the dynamic linker when the
static lib is used.

### Shared and static libraries

Sometimes, you may want to explicitly specify in the build file whether to
create a [shared](../reference/builtins.md#shared_library) or a
[static](../reference/builtins.md#static_library) library. This is easy to
accomplish:

```python
shared = shared_library('shared', files=['shared.cpp'])
static = static_library('static', files=['static.cpp'])
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

## Generated sources

In addition to compiling and linking, many build involve a source-generation
step, e.g. generating lexers/parsers via Lex/Yacc. bfg9000 tries to make this as
simple as possible. Much like how
[*executable()*](../reference/builtins.md#executable) (and
[*library()*](../reference/builtins.md#library), etc) will automatically invoke
[*object_files*](../reference/builtins.md#object_files) as needed to create the
compilation steps, bfg9000 will automatically add the appropriate
[*generated_source()*](../reference/builtins.md#generated_source) calls where
possible.

Here, since `'qml.qrc'` can be auto-detected as a Qt QRC file, the `'qml.cpp'`
file will be created and passed on to the implicit
[*object_file*](../reference/builtins.md#object_file) call:

```python
executable('qtprog', ['main.cpp', 'qml.qrc'], ...)
```

However, there are situations where this doesn't work automatically. Some
source-generation steps, such as Yacc, output multiple files, so they can't be
invoked implicitly:

```python
parse, parse_h = generated_source(file='calc.y')
executable('calc', files=[parse, ...], includes=[parse_h])
```

In addition, bfg9000 can only invoke
[*generated_source()*](../reference/builtins.md#generated_source) automatically
when the file is passed as the source to be compiled by
[*object_file*](../reference/builtins.md#object_file). Using a Qt UI file, for
example, requires explicitly generating the source:

```python
widget = generated_source('widget.ui')
executable('qtprog, ['main.cpp'], includes=[widget], ...)
```

Finally, some source-generators don't have their own unique file extensions, so
it's not possible to automatically detect their language. In this case, you can
either explicitly call
[*generated_source()*](../reference/builtins.md#generated_source) or create the
file object with the appropriate language, e.g.:
`auto_file('window.hpp', lang='qtmoc')`.

## Finding files

For projects with many source files, it can be inconvenient to manually list all
of them. Since `build.bfg` files are just Python scripts, you *could* use
Python's standard library to examine the file system and build the list.
However, there's a better way: bfg9000 provides a
[*find_files()*](../reference/builtins.md#find_files) function to fetch the
list; if the list ever changes, the build files will be regenerated
automatically the next time they're run.

*find_files()* starts at a base directory and searches recursively for any files
matching a particular glob:

```python
hello_files = find_files('src/hello/**/*.cpp')
executable('hello', files=hello_files)
```

There are lots of options you can pass to *find_files()* to tweak its behavior.
For instance, you can exclude certain files or directories by passing a glob to
the *exclude* argument.

## Default targets

When you're building multiple binaries, you might want to be able to specify
what gets built by default, i.e. when calling `make` (or `ninja`) with no
arguments. Normally, every executable and library (except those passed to
[*test()*](../reference/builtins.md#test)) will get built. However, you can pass
any build steps to [*default()*](../reference/builtins.md#default), and they'll
be set as the default, overriding the normal behavior. This makes it easy to
provide your users with a standard build that gets them all the bits they need,
and none they don't.

## External packages

Most non-trivial projects have external package dependencies. These can be
specified in a `build.bfg` file via
[*package()*](../reference/builtins.md#package) and used when building binaries
by passing them in the *packages* argument:

```python
ogg = package('ogg', kind='static')
prog_opts = package('boost', 'program_options', version='>=1.55')

executable('program', files=['main.cpp'], packages=[ogg, prog_opts])
```

There are many different ways external packages are distributed, but for native
packages (C, C++, Fortran, etc), this is handled via [mopack][mopack]. mopack
provides a variety of ways to resolve external packages, and bfg9000 will
automatically invoke mopack during configuration. You can specify how each
package dependency should be resolved via an `mopack.yml` file:

```yaml
packages:
  foobar:
    origin: tarball
    path: foobar-1.0.tar.gz
    build: bfg9000
```

By keeping the package resolution metadata separate from the `build.bfg` file,
it's much easier for people building your project to override how package
dependencies are resolved.

## Installation

After building, you might want to allow your project to be installed onto the
user's system somewhere. Most files (headers, executables, libraries) can be
added to the list of installed files via the
[*install()*](../reference/builtins.md#install) function. You can also install
entire directories of headers:

```python
include_dir = header_directory('include')
lib = static_library('program', files=['src/prog.cpp'], includes=[include_dir])
install(lib, include_dir)
```

## Tests

All good projects should have tests. Since your project is good (isn't it?),
yours has tests too, and you should have a good way to execute those tests from
your build system. bfg9000 provides a [set of
functions](../reference/builtins.md#test-steps) for running tests. The most
important of these is aptly named [*test()*](../reference/builtins.md#test). Any
executable can be passed to this function, and it will be executed as a test; an
exit status of 0 marks success, and non-zero marks failure:

```python
test( executable('test_foo', files=['test_foo.cpp']) )
```

In addition, you can provide a [test
driver](../reference/builtins.md#test_driver) that collects all of your tests
together and runs them as one. *test_driver()* takes an executable (a
[*system_executable*](../reference/builtins.md#system_executable) by default)
that runs all the test files. This allows you to aggregate multiple test files
into a single run, which is very useful for reporting:

```python
mettle = test_driver('mettle')
test( executable('test_foo', files=['test_foo.cpp']), driver=mettle )
test( executable('test_bar', files=['test_bar.cpp']), driver=mettle )
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

## Commands

In addition to ordinary build steps, it can be useful to provide other common
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

## Submodules

For larger projects, putting all of your build configuration in a single file
can be difficult to maintain. Instead, you can split your configuration into
multiple submodules. The [*submodule*](../reference/builtins.md#submodule)
function will execute the `build.bfg` file (or `options.bfg` file [when
applicable](#user-defined-arguments)) in the specified directory and return any
exported objects as a dict to be used in the parent module. The submodule can
then call the [*export*](../reference/builtins.md#export) function to return any
relevant objects (e.g. built files) to the parent module:

```python
# In main build.bfg:
sub = submodule('dir')
executable('exe', ['exe.cpp'], libs=[sub['library']])

# In sub/build.bfg:
lib = library('mylib', ['mylib.cpp'])
export(library=lib)
```

Within a submodule, all paths for inputs (source files) and outputs (built
files) are relative to the directory containing the submodule's `build.bfg`
file. (If you need to reference a file outside of the submodule's directory, you
can simply prefix your path with `../`):

```python
# In sub/build.bfg:

# Builds $(builddir)/libmylib.so (or similar) from $(srcdir)/sub/mylib.cpp:
library('../mylib', ['mylib.cpp'])
```

## Custom build steps

Sometimes, the built-in build steps don't support the things you want to do
(e.g. if you're generating source files via Flex/Bison). In these cases, you
can use [*build_step()*](../reference/builtins.md#build_step) to define a step
that produces a file by running an arbitrary command:

```python
lex = build_step('lex.yy.c', cmd=[ 'flex', source_file('hello.lex') ])
```

To reduce repetition, you can also use the `build_step.input` and
`build_step.output` placeholders in your command.

```python
lex = build_step('hello-lex.c', cmd=[
    'flex', build_step.input, '-o' build_step.output
], files=['hello.lex'])
```

By default, the output of a custom build step is passed through
[*auto_file*](../reference/builtins.md#auto_file), which produces a source file,
header file, or a generic file based on the path's extension. When this doesn't
produce the expected results, you can supply the *type* argument, which lets you
pass a function taking a path and returning a file object to represent the
output:

```python
libfoo = shared_library(...)
stripped = build_step('libfoo.so', cmd=[
    'strip', '-o', build_step.output, libfoo
], type=shared_library)
```

Finally, you can define steps that produce *multiple* files by passing a list of
names as the outputs of the step. This will then return a file object for each
of the outputs:

```python
hdr, src = build_step(['hello.tab.h', 'hello.tab.c'], cmd=[
    'bison', source_file('hello.y')
])
```

When producing multiple files via *build_step*, the *type* argument can be
passed as either a single function (which will be applied to every output) or as
a list of function (which will be applied element-wise to each output).

## User-defined arguments

Many projects benefit from letting the user configure project-specific elements
of their builds, e.g. by enabling certain optional features or by using
different branding for testing and release builds. You can add support for
options to configure your build by creating a `options.bfg` file alongside your
`build.bfg`.

Inside `options.bfg`, you can define arguments with the
[*argument()*](../reference/builtins.md#argument) function:

```python
# Adds --name/--x-name to the list of available command-line options, e.g.:
#   9k build/ --name=foobar
argument('name', default='unnamed', help="set the program's name")
```

It works much like [argparse][argparse]'s [*add_argument()*][add_argument]
method, except that a) argument names are automatically prefixed with `--` (and
`--x-` for forwards compatibility) and b) there are two extra actions available:
`enable'` and `'with'`:

```python
# Adds --enable-foo/--disable-foo (and --x- variants)
argument('foo', action='enable', help='enable the foo feature')

# Adds --with-bar/--without-bar (and --x- variants)
argument('bar', action='with', help='build the bar module')
```

Once these options are defined, you can fetch their results from the built-in
[*argv*](../reference/builtins.md#argv) global in your `build.bfg` file. This
object is simply an [*argparse.Namespace*][namespace] object:

```python
print("This program's name is {}".format(argv.name))

if argv.foo:
    pass  # Enable the foo feature
if argv.bar:
    pass  # Build the bar module
```

## Generating pkg-config data

When creating libraries for other projects to use, [`pkg-config`][pkg-config] is
a common tool to simplify using the library. `pkg-config` allows users to look
up a package and retrieve all the compiler and linker options required to use
that package. You can generate a `pkg-config` `.pc` file using the
[*pkg_config()*](../reference/builtins.md#pkg_config) function:

```python
project('my_project', '1.0')

include = header_directory('include', include='*.hpp')
lib = library('hello', files=['src/hello.cpp'], includes=[include])

install(lib, include)

pkg_config(
    'my_pkgconfig_project',
    version='2.0',
    includes=[include],
    libs=[lib],
)
```

If the *auto_fill* parameter is *True*, this function will automatically fill
in the values for the package's name, version, installed include directories,
and installed libraries:

```python
pkg_config(auto_fill=True)
```

You can even use the pkg-config package you just created when building other
binaries. However, this is only allowed when *auto_fill* is *False*, since
bfg9000 won't know what an auto-filled `pkg-config` `.pc` file would look like
until after the build script is finished:

```python
my_pkg = pkg_config(
    # ...
)

executable('prog', 'prog.cpp', packages=[my_pkg])
```

Libraries are perhaps the most interesting part of the *pkg_config()* function.
If a library listed here depends on any packages or other libraries, they will
automatically be included in the `pkg-config` info.

There are several other options available to tweak the output of this function,
detailed in the [reference guide](../reference/builtins.md#pkg_config).

[mopack]: https://jimporter.github.io/mopack/
[pkg-config]: https://www.freedesktop.org/wiki/Software/pkg-config/
[argparse]: https://docs.python.org/library/argparse.html
[add_argument]: https://docs.python.org/library/argparse.html#the-add-argument-method
[namespace]: https://docs.python.org/library/argparse.html#argparse.Namespace
