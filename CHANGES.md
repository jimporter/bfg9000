# Changes

## v0.7.0 (2023-05-20)

### New features
- Add support for resolving external package dependencies via [mopack][mopack]
- Add `bfg9000 run` command to allow executing other commands using the
  environment variables for a given build
- Add support for installing man pages
- Add `--datadir` and `--mandir` configuration options
- Create `compile_commands.json` when generating build scripts
- `pkg-config` executable can now be found by guessing based on other compilers
- Compiler and tool objects now have a `found` property to indicate if they were
  found on the system
- Add `system` flag to `package()` and `pkg_config()` to determine whether to
  treat include directories from packages as system directories
- Add `bfg9000 generate-completion` to generate shell-completion functions
- Add support for `CLICOLOR` and `CLICOLOR_FORCE` environment variables to
  control whether to display colors in terminal output

### Breaking changes
- Require Python 3.6+
- Qt dependencies are now specified via `package('Qt', '<component>')` rather
  than `package('Qt<component>')`
- bfg9000 no longer automatically installs `patchelf` on Linux systems

### Bug fixes
- Error reporting now shows the proper stack frames on Windows
- Fix detection of `clang-cl` compiler
- MinGW can now use libraries of the form `name.lib`
- Paths with basenames of `.` or `..` are now treated as directories
- Improve support for detecting tool versions when generating MSBuild files
- Empty strings as command-line arguments (e.g. in `command`) are now properly
  quoted
- *pkg-config* `.pc` files now always use POSIX-like paths
- Fix display of the traceback in a bfg file when building from the build
  directory
- Replace `packaging` dependency with `verspec` for future stability

[mopack]: https://jimporter.github.io/mopack/

---

## v0.6.0 (2020-09-12)

### New features
- Add support for including multiple `build.bfg` (and `options.bfg`) files from
  subdirectories via `submodule()`
- Create `-uninstalled` variants of generated *pkg-config* `.pc` files and
  allow build scripts to use them internally
- Add `opts.gui` to generate graphical programs (important on Windows)
- Add `opts.static` to request static linking of libraries
- MSVC's runtime can now be selected by using a combination of `opts.static`
  and `opts.debug`
- MSVC linker now automatically links to default Windows libraries
  (`kernel32.lib`, etc)
- Link steps (`executable`, `library`, etc) now accept an `extra_compile_deps`
  argument to forward on to the compilation step
- Allow customizing `install` locations for specific files via the `directory`
  argument
- Iterables passed to `default` or `install` will include each element of the
  iterable in the appropriate build target
- `info()`, `debug()`, and `warning()` now take a variable number of arguments
  to print
- `generated_source()` steps are now automatically created as necessary for
  files passed to `object_file()`, if possible
- Add `path_exists()` builtin
- Paths with a trailing `/` are now treated as directory paths, and when passed
  to `auto_file()` will create a directory object
- Add support for compiling Windows `.rc` files
- Add support for setting the entry point for native binaries (C, C++, etc)
- The default list of excluded globs for `find_files()` can now be customized
  via `project(find_exclude=[...])`
- Try to find the right compiler to use for C-family languages by guessing based
  on other compilers in the family (e.g. if `CXX=g++`, guess that the C compiler
  is `gcc`)
- Add support for `DESTDIR` on Windows when installation paths don't include a
  drive letter
- Regenerating build files with the Ninja backend now uses the `console` pool,
  allowing realtime output and colored text

### Breaking changes
- Drop support for Python 2
- `find_files()` and `find_paths()` have been redesigned to support recursive
  globs
- `pkg_config()` now defaults to `auto_fill=False`
- `resource_file()` has been deprecated; use `source_file()` instead
- `show_stack` for `info()` and `debug()` must now be specified as a keyword
  argument
- `directory`, and `header_directory` now require uncommon arguments to be
  specified as keyword arguments
- Adding to existing environment variables in `env.execute()` and `env.run()`
  is now done via `extra_env`, not `env`/`env_update`

### Bug fixes
- `copy_file()` now works correctly when copying into a subdirectory on the
  Make backend
- `extra_deps` now works with `copy_file()`
- Calling `exit()` with a non-zero return code from a `build.bfg` file now
  causes configuration to fail
- Automatically-generated PCH source files (for MSVC compilers) are now placed
  in the same directory as the resulting PCH
- The contents of header directories in the build directory are now installed to
  the base include directory
- The `install_name` for libraries on macOS is now always an absolute path,
  instead of using `@rpath`-based paths prior to installation
- MSBuild backend can now build libraries with no source files that link to a
  whole-archive library
- Object files with unrecognized source languages can now be linked with the
  default linker for their object format
- `.stamp` files generated by the Make backend are now properly removed when
  running `make clean`
- Fix `sudo` prompt when installing to a system directory with the Ninja backend

---

## v0.5.1 (2019-12-07)

### Bug fixes
- Depfiles generated by compile steps are now properly included into Makefiles
- Include directories passed to via `include` and libraries passed via `libs`
  are now listed before those from `packages` when building
- Fix linking to shared libraries located in the source directory

---

## v0.5.0 (2019-11-25)

### New features
- Add `generated_source()` to allow generating source code from domain-specific
  languages
- Add support for `lex`, `yacc`, and Qt build tools (`moc`, `rcc`, `uic`)
- Add the ability to use placeholders for `build_step()` and `command()`
- Add an `auto_file()` function that infers the kind of file based on its
  extension; `build_step()` now uses this by default for outputs
- Add `always_outdated` argument to `build_step()`
- Add `copy_file()` and `copy_files()` functions
- `default()` now returns the files passed into it
- `install()` now returns the installed forms of the files passed into it
- Add `safe_str()` and `safe_format()` to help safely build command string
- Expose `Path` object to bfg scripts
- Add `directory` as an option for `object_file()`, `generated_source()`,
  `copy_file()`, and their list-variants
- Add `lang` and `intermediate_dirs` arguments to `project()` for modifying
  project-wide settings
- Add `srcdir` builtin to toolchain files

### Breaking changes
- `find_files()` redesigned and split into `find_files()` and `find_paths()`;
  simple cases should still work, but more complex uses will need adjusted
- *pkg-config* `.pc` files generated by bfg9000 no longer include rpath flags
- Explicitly passing `lang` to a build step now overrides the languages of any
  input files when determining the builder
- `args` and `kwargs` no longer supported for `build_step()`; use a lambda
  instead
- Options specified on the command line (e.g. install locations) now override
  settings in toolchain files
- Implicitly-defined object files (e.g. those generated by `executable()`) are
  placed in an intermediate directory; call `project(intermediate_dirs=False)`
  to disable this

### Bug fixes
- Include `options.bfg` in dist tarballs
- Fix escaping of `~` in Makefiles
- Symbolic links (e.g. from versioned shared libraries) are now properly
  installed as symlinks
- Generated header directories are now included as dependencies of compilation
  steps
- Default install locations are now based on the *target* platform instead of
  the host platform, with cross-platform builds defaulting to installation
  disabled
- Shared libraries with `soversion`s can now be used with `pkg_config()`

---

## v0.4.1 (2019-07-05)

### Bug fixes
- Fix using semantic options in `global_options`

---

## v0.4.0 (2019-07-05)

### New features
- Compilers and linkers now support semantic options, abstracting away the
  differences between compiler flavors
- Add support for cross-compilation
- Toolchain files can be used to simplify setting up build configuration
  options
- Add `info`, `warn`, and `debug` builtins to let build scripts print messages
  via bfg's logging system
- `whole_archive()` now works with MSVC linkers
- Add support for module-definition files when linking `.exe` or `.dll` files
- Build steps now have a (customizable) friendly description when using the
  Ninja backend
- Makefiles generated by bfg now have a `clean` target

### Breaking changes
- MSVC builds now automatically set `/EHsc` to improve standards-compliance and
  mimic Visual Studio's default MSBuild configuration
- Paths are now parsed in a platform-agnostic manner, which may cause issues for
  certain esoteric pathnames (e.g. POSIX paths that look like Windows paths)
- `env.platform` has been split into `env.host_platform` and
  `env.target_platform`
- MinGW now makes DLLs named `<name>.dll` instead of `lib<name>.dll`
- Platform names are reworked; `'windows'` is now `'winnt'` and `'darwin'` is
  `'macos'`

### Bug fixes
- Fix support for packaging as a Python Wheel
- Default options for `ar` are now `cr` instead of `cru` to support versions of
  `ar` that default to deterministic builds
- Fix building Java projects with OpenJDK 8+
- Fix loading Boost packages from `C:\Boost` on Windows
- Libraries are linked via their absolute paths where possible to help
  disambiguate libraries with the same name

---

## v0.3.1 (2018-06-01)

### Bug fixes
- Fix an issue with creating the build directory during the configuration
  process

---

## v0.3.0 (2018-06-01)

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

## v0.2.0 (2016-06-26)

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

## v0.1.1 (2016-01-21)

- Fix an issue with installing the package from PyPI

---

## v0.1.0 (2016-01-20)

- Initial release
- Support for C and C++ builds on Linux, Mac, and Windows (MinGW included) via
  Make, Ninja, and MSBuild.
