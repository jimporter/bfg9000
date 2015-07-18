# How to Use bfg9000 on Windows

Since bfg9000 is a command-line program, you'll need to open a command prompt.
However, since the MSVC tools aren't in the path by default, you need to pick
the *correct* prompt to open. Visual Studio provides Start Menu links such as
"VS2015 Developer Command Prompt". These add the appropiate directories to the
`PATH`, allowing you to use the version of the MSVC tools that you'd like.

## Setting options

Many options for building can be set via the environment. These generally follow
the UNIX naming conventions, so you can use `CFLAGS`, `CXXFLAGS`, and `CPPFLAGS`
for compilation flags, `LDFLAGS` for linker flags, and `LIBRARY_PATH` for the
list of library search directories.
