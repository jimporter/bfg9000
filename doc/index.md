# bfg9000

**bfg9000** (*"build file generator"*) is a cross-platform *build configuration
system* with an emphasis on making it easy to define how to build your software.
It converts a Python-based build script into the appropriate files for your
underlying build system of choice.

## Why bfg9000?

---

#### Already familiar

`build.bfg` files are just Python scripts with some new functions added, so you
may already know how to write them; and when your build gets complicated, you
can rely on the existing Python ecosystem to get you out of trouble.

#### Build fast

Python may be slow, but bfg9000 gets out of the way as quickly as possible and
relies on existing, mature build systems like Make and Ninja to do the heavy
lifting of building your software.

#### Stay sane

Building your code shouldn't be the hard part of developing your project. Above
all else, bfg9000 strives to make it easy to write your build scripts.

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

For further examples, please see the
[`examples/`](https://github.com/jimporter/bfg9000/tree/master/examples)
subdirectory.
