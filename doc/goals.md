# Design Goals

**bfg9000**'s primary goal is to be a good build configuration system, *not*
a build system itself. It's designed to compete with, for instance, autotools
and CMake, and coexists with tools like Make and Ninja.

## Goals

### Be a configuration system, not a build system

There are lots of good build systems out there (Tup, Ninja), and lots that have
the benefit of ubiquity on their platform (Make, MSBuild, Xcode). Heck, when you
stop trying to use Make as a build configuration system, it too is a pretty
decent build system (although performance can suffer for large projects).
Therefore, bfg9000 can rely on these tools to - hopefully efficiently - perform
the actual builds, leaving bfg to be responsible solely for compiling a
configuration-specific build file.

After initial configuration, users will interact only with the underlying build
system, allowing us to avoid many of the issues with Python's slowness. In
practice, bfg will only need to be re-invoked if a file is added or removed,
which is relatively rare.

### Support multiple build systems

The build system you choose often depends on your platform. A Linux user will
probably want a tool like Make or Ninja, whereas a Windows user might want a
Visual Studio project. We should support this (keeping in mind that not every
backend will support every feature bfg can provide).

### Provide access to multiple targets for a given config

It's useful to have multiple targets for a build, such as `make all`,
`make test`, `make install`, or other more special-purpose ones, like
`make doc`. This should be supported so that common tasks in a project are easy.
Some commands are entirely disjoint from each other (e.g. `make all` vs
`make doc`), so it could make sense for them to be separate configurations, but
this may not be necessary.

### Allow the creation of custom build steps

A good build system needs a good way to create custom steps in a configurable
way (e.g. running lex/yacc; a user might want to specify flex/bison instead). It
should be easy for users to make these build steps and provide them to the
config file. This might mean allowing bfg to use additional libraries, but that
could complicate the config process for users (they'd need to download the
additional library before configuring).
