# bfg9000 - build file generator

**bfg9000** (sometimes just **bfg**) is currently a plan for a next-generation
build configuration system. It's designed to replace things like autotools and
Cmake, *not* things like Make and Ninja.

## Requirements

### Be a configuration system, not a build system

Build systems are already a solved problem. There are lots of good ones (Tup,
Ninja), and lots that have the benefit of ubiquity on their platform (Make,
MSBuild, Xcode). This allows us to generate the build files once, possibly using
complex rules, and then use a simple-but-fast tool to perform the actual builds.
Regenerating the build files would only need to happen if a file is added or
removed, which is relatively rare.

### Use an existing general-purpose language

This simplifies both the development and use of bfg. There's no need to design
or learn a new syntax, and more complicated build scripts can take advantage of
existing libraries for the language. The current leading contender for language
is Python, since it works on all major platforms, is well-known, and has
reasonably nice syntax. Haskell is another option, but it's less well-known and
harder to set up on some systems.

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

## Open Questions

### How closely should bfg match the build process?

For instance, should bfg have separate steps for compiling and linking? This is
more flexible, but the flexibility wouldn't be needed very often.

### Should bfg require out-of-tree builds?

Out-of-tree builds are generally a good idea, since they make it easier to build
a project with multiple configurations (e.g. debug, release). Should we require
this? It would simplify cleaning a build (just remove the directory).

## License

This project is licensed under the BSD 3-clause license.
