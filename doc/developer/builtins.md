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
for `build.bfg` files, `'options'` for `options.bfg` files, `'toolchain'` for
`<toolchain>.bfg` files, and `'*'` for all files; in addition, you can specify
a list of any of these strings to add the object to multiple contexts.

### @default([*context*], [*name*]) { #default }

Define a function (or other callable object, including a type) as a builtin for
the specified *context*s. If *name* is passed, it will be used as the builtin's
name; otherwise, the function's name will be used.

### @function([*context*], [*name*]) { #function }

Define a function (or other callable object) as a builtin for the specified
*context*s. If *name* is passed, it will be used as the builtin's name;
otherwise, the function's name will be used. When called by a bfg script, the
function will be passed a [context object](#context-objects) as the first
argument.

### @getter([*context*], [*name*]) { #getter }

Define a getter function as a builtin for the specified *context*s. If *name* is
passed, it will be used as the builtin's name; otherwise, the function's name
will be used. When called by a bfg script, the function will be passed a
[context object](#context-objects) as the first argument.

### @post([*context*], [*name*]) { #post }

Define a function to be run after the user's build script is executed for the
specified *context*s. When called after a bfg script, the function will be
passed a [context object](#context-objects) its only argument.

### @type(*out_type*, [*in_type*], [*extra_in_type*], [*short_circuit*], [*first_optional*]) { #type }

Define the return type of the decorated function as *out_type* and accepting
automatic conversion of any object of *in_type* or *extra_in_type* (either a
type or tuple of types, defaulting to *string_or_path_types*) as the first
argument. If *short_circuit* is true (the default), passing in an object of type
*out_type* will simply return the input with no changes. If *first_optional* is
true, calling the decorated function with a single positional argument will pass
*None* as the first argument, and the supplied argument as the second.

This decorator is primarily useful for autoconversion of strings to the
corresponding object for one of a build step's arguments (e.g. converting
`'foo.cpp'` to a *SourceFile*).

## Context objects

Context objects contain all the necessary data to manage the internal state
corresponding to a bfg script. These can be used by builtins to work with the
environment, add build steps to the graph, etc.

[github-issue-48]: {{ config.repo_url }}issues/48
[builtins]: {{ repo_src_url }}bfg9000/builtins
