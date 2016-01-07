# Developer Documentation

At its core, a build file is just a DAG (directed acyclic graph) that gets
walked through by the build system, where the nodes are files and the edges are
build steps. A bfg9000 build file is no different.

## How a build.bfg file is compiled

### Snapshot the environment

When bfg9000 is invoked, it first takes a snapshot of the current environment
(the operating system, environment variables, compiler to use, etc). This is
important to provide a stable state for regeneration of the build file if
necessary (e.g. if build.bfg is changed).

### Build an internal dependency graph

Next, it executes the build.bfg file. Most bfg9000 functions represent build
steps or other related parts of the dependency graph. When called, these build
up an internal DAG structure with all the backend-agnostic data filled in (e.g.
virtual filenames are resolved to real ones, such as "foo" to "libfoo.so").

### Emit the final build file

Once this is complete, the DAG is passed to the appropriate backend, which
iterates over all the known edges (build steps) and emits the backend-specific
code for them. Since all the backends handle walking the DAG on their own,
bfg9000 can safely avoid worrying about trying to do this efficiently in Python.
