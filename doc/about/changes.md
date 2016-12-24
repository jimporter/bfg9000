# Changes

## v0.3.0
in progress
{: .subtitle}

### New features

- Add `header` argument to `system_package()` to find header files
- Support Java/Scala
- Add support for user-defined arguments

---

## v0.2.0
2016-06-26
{: .subtitle}

### New features
- Support Objective C/C++
- Partially support Fortran (simple projects work, but more complex things
  probably don't)
- Improved error reporting
- Warn users if necessary build tools can't be found by bfg9000
- Automatically include runtime dependencies when installing a binary
- Support `@rpath` on OS X
- Allow fetching bfg's version from `build.bfg` files via *bfg9000_version*
- Support versioning of shared libraries on POSIX systems
- Support resolving packages via pkg-config
- Locally-built static libraries now forward their options to binaries that link
  to them
- *whole_archive* now forwards its arguments on to *static_library*
- Use *doppel* for installing files instead of *install(1)*
- Support *command* and *alias* rules under MSBuild
- Add support for building a distribution of the sources (`make dist`)
- Allow running custom build steps via `build_step()`

### Breaking changes
- Configuring a build is now performed by `bfg9000 configure DIRECTORY`
- `header()` renamed to `header_file()`
- `env.compiler(lang)` replaced by `env.builder(lang).compiler`
- `env.linker(lang, mode)` replaced by `env.builder(lang).linker(mode)`
- `env.compiler(lang).flavor` replaced by `env.builder(lang).flavor`

### Bug fixes
- Fix fetching `CFLAGS` from the environment (it used to try `CCFLAGS`)
- Fix execution context of `build.bfg` files; this caused strange issues with
  list/generator comprehensions

---

## v0.1.1
2016-01-21
{: .subtitle}

- Fix an issue with installing the package from PyPI

---

## v0.1.0
2016-01-20
{: .subtitle}

- Initial release
- Support for C and C++ builds on Linux, Mac, and Windows (MinGW included) via
  Make, Ninja, and MSBuild.
