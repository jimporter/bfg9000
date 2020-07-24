# Build Backends

bfg9000 supports generating files for multiple build tools, called "backends".
These are specified in the `bfg9000.backends` [entry point][entry-point]; third
parties can add support for their own backend by hooking into this.

!!! warning
    Currently, custom build steps aren't supported as [builtins](builtins.md);
    however, support is planned, and any third-party backend will need to
    decide which (if any) custom build steps they'd like to support.

## How a build.bfg file is compiled

Before we get started looking at how each bakend works, let's quickly go over
how a `build.bfg` file is compiled at a high level. At its core, a build file is
just a DAG (directed acyclic graph) that gets walked through by the build
system, where the nodes are files and the edges are build steps. A bfg9000 build
file is no different.

### Snapshot the environment

When bfg9000 is invoked, it first takes a snapshot of the current environment
(the operating system, environment variables, compiler to use, etc). This is
important to provide a stable state for regeneration of the build file if
necessary (e.g. if `build.bfg` is changed).

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

## Public API for backends

### backend.write(*env*, *build_inputs*) { #backend-write }

Called when bfg9000 has finished building its internal dependency graph and it's
time to generate the backend-specific build files. *env* is an
[*Environment*](../reference/builtins.md#environment) object and *build_inputs*
is a *BuildInputs* object containing the internal dependency graph.
`build_inputs.edges()` returns a list of *Edge*s that correspond to each build
step defined in the `build.bfg` file.

### backend.priority { #backend-priority }

The priority of this build backend. This helps determine the default backend.
The default is the backend with the highest priority that's also "valid" (i.e.
[`backend.version()`](#backend-version) returns a non-*None* value).

### backend.version() { #backend-version }

Return the version (as a [*packaging.LegacyVersion*][packaging-legacy-version]
object -- also aliased as `bfg9000.versioning.Version`) of this build backend's
underlying tool. If the tool can't be found (or is otherwise broken), this
returns *None*.

[entry-point]: https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins
[packaging-legacy-version]: https://packaging.pypa.io/en/latest/version/#packaging.version.LegacyVersion
