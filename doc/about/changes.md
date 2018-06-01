# Changes

## v0.4.0
in progress
{: .subtitle}

No changes yet!

---

## v0.3.1
2018-06-01
{: .subtitle}

### Bug fixes
- Fix an issue with creating the build directory during the configuration
  process

---

## v0.3.0
2018-06-01
{: .subtitle}

### New features
- Replace `system_package()` and `pkgconfig_package()` with a generic package
  resolver: `package()`
- Add `headers` argument to `package()` to find header files and `libs` to
  specify library names if *pkg-config* lookup fails
- Support Java/Scala
- Add support for user-defined arguments
- Add a `library()` function that builds shared and/or static libraries per the
  user's preference
- Add support for generating *pkg-config* `.pc` files
- Allow executing files that require an interpreter or other wrapper via
  `command()` or `test()`/`test_driver()` without explicitly specifying the
  wrapper; supports all languages buildable by bfg9000, plus Lua, Perl, Python,
  and Ruby
- Add `env.run()`, `env.execute()`, and `env.run_arguments()` to simplify
  executing programs during configuration
- Add a `framework()` function to specify macOS frameworks to use for a build
- Improve detection of compiler flavors by checking version information
- Automatically colorize clang/gcc output under Ninja
- Add support for uninstalling builds
- Add `static_link_options` to `static_library()` to specify options to pass to
  the static linker
- Add a `bfg9000 env` command to print the environment variables used during
  configuration
- Automatically request sudo elevation when installing builds to a system
  directory

### Breaking changes
- `directory()` and `header_directory()` no longer automatically include all
  files within them (pass `include='*'` for the old behavior)
- The `include` argument for compiling object files has been replaced by
  `includes`
- When creating a static library, `link_options` now specifies options that will
  be forwarded along to the dynamic linker, rather than options for the static
  linker itself
- The `options` argument for `test()`/`test_driver()` has been deprecated; add
  any options to the first argument (`cmd`) instead
- `test()` no longer converts its first argument to a `generic_file()`
- Splitting POSIX shell strings (used for compile and link options as well as
  environment vars on POSIX like `CPPFLAGS`) no longer parses escape characters

### Bug fixes
- Improve logging of syntax errors in `build.bfg` files
- Fix usage of nested shared libraries when linking with GNU ld (via
  `-rpath-link`)
- Installing directories from the srcdir now correctly installs their contents
  to the installation root for that type (e.g. a header directory of `foo/bar`
  installs its contents to `$includedir`)
- Fix generation of dependencies for the `tests` target
- Improve escaping for paths when using Make on Windows (previously users had
  to escape backslashes themselves)
- Fix an issue with quotation marks being stripped for some commands on Windows
  with the Ninja backend

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
- Allow fetching bfg's version from `build.bfg` files via `bfg9000_version`
- Support versioning of shared libraries on POSIX systems
- Support resolving packages via pkg-config
- Locally-built static libraries now forward their options to binaries that link
  to them
- `whole_archive()` now forwards its arguments on to `static_library()`
- Use *doppel* for installing files instead of *install(1)*
- Support `command()` and `alias()` rules under MSBuild
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
