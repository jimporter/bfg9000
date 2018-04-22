# Builtins

!!! note
    Builtins aren't currently extendable by third parties. However, this is
    [planned][github-issue-48].

bfg9000 provides a set of builtin functions, classes, and variables to build
scripts so that projects can easily describe their build process. These are
all defined in [`bfg9000/builtins/`][builtins]; each file is automatically
imported and its builtins are added to a dict of globals to pass to `build.bfg`.

## Decorators

Builtins are defined by using decorators defined in `bfg9000.builtins.builtin`;
by default, these make the decorated object available to `build.bfg`, but you
can also specify the context to change where the object is available: `'build'`
for `build.bfg` files, `'options'` for `options.bfg` files, and `'*'` for all
files.

These decorators also accept a list of internal global variables to be passed
to the decorated function. For *build* contexts, valid globals are
`build_inputs`, `env`, and `argv`; for *options* contexts, `env` and `parser`.

### @function(*global*, ..., [*context*]) { #function }

Define a function (or other callable object, including a type) as a builtin with
the specified *global*s passed as the initial arguments to the function.

### @getter(*global*, ..., [*context*]) { #getter }

Define a getter function as a builtin with the specified *global*s passed as
the initial arguments to the function.

### @post(*global*, ..., [*context*]) { #post }

Define a function to be run after the user's build script (`build.bfg` or
`options.bfg`, depending on *context*) is executed.

### @type(*out_type*, [*in_type*]) { #type }

Define the return type of the decorated function as *out_type* and accepting
automatic conversion of any object of *in_type* (either a type or tuple of
types, defaulting to *string_types*) as the first argument. This is primarily
useful for autoconversion of strings to the corresponding object for one of a
build step's arguments (e.g. converting `'foo.cpp'` to a *SourceFile*).

[github-issue-48]: https://github.com/jimporter/bfg9000/issues/48
[builtins]: https://github.com/jimporter/bfg9000/tree/master/bfg9000/builtins
