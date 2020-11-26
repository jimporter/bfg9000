# bfg9000

**bfg9000** (*"build file generator"*) is a cross-platform *build configuration
system* with an emphasis on making it easy to define how to build your software.
It converts a Python-based build script into the appropriate files for your
underlying build system of choice.

## Why bfg9000?

---

#### Familiar syntax

`build.bfg` files are just Python scripts with some new functions added, so you
may already know how to write them; and when your build gets complicated, you
can rely on the existing Python ecosystem to get you out of trouble.

#### Fast builds

bfg9000 ensures your builds are fast by relying on existing, mature build
systems like Make and Ninja to do the heavy lifting of building your software;
often, incremental builds don't need to execute bfg9000 at all!

#### Stay sane

Building your code shouldn't be the hard part of developing your project. Above
all else, bfg9000 strives to help you get your build right the *first* time with
many helpful [features](user/features.md).

---

## A brief example

You can't get much simpler than the simplest `build.bfg` file:

```python
executable('simple', files=['simple.cpp'])
```

To build this executable, we need to create the actual build files and then
run them:

```sh
$ cd /path/to/src/
$ 9k build/
$ cd build/
$ ninja
```

From there, you can run your newly-created executable: `./simple`. Hooray!

For further examples, please see the [`examples/`][examples] subdirectory.

[examples]: {{ repo_src_url }}examples
