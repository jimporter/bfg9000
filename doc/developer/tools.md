# Build Tools

!!! note
    Build tools aren't currently extendable by third parties. However, this is
    [planned][github-issue-48].

As a build configuration system, bfg9000 naturally interacts with many other
tools; this interaction is defined for each tool in [`bfg9000/tools/`][tools];
each file is automatically imported and the tools are added to a dict ultimately
used by the [*environment object*](../user/reference.md#environment-object).

## Decorators

### @builder(*lang*, ...)

Define a builder for one or more *lang*s. The API for builders is somewhat
complex and currently beyond the scope of this document.

### @tool(*name*, [*lang*])

Define a tool named *name* that optionally acts as a runner for files with the
language *lang*. The API for tools is somewhat complex and currently beyond the
scope of this document.

## Accessors

### get_builder(*env*, *lang*)

Get the builder associated with *lang*, passing *env* (and *lang* if the builder
was defined for multiple languages) to the builder type.

### get_tool(*env*, *name*)

Get the tool named *name*, passing *env* to the tool type.

### get_tool_runner(*lang*)

Get the name of the tool specified to run files with language *lang*.

[github-issue-48]: https://github.com/jimporter/bfg9000/issues/48
[tools]: https://github.com/jimporter/bfg9000/tree/master/bfg9000/tools
