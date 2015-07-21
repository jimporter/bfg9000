# bfg9000 - build file generator

**bfg9000** is a cross-platform *build configuration system* with an emphasis on
making it easy to define how to build your software. It converts a Python-based
build script into the appropriate files for your underlying build system of
choice (Make, Ninja, or MSBuild).

## Installation

bfg9000 uses setuptools, so installation is much the same as any other Python
package. Just run:

```sh
python setup.py install
```

## A Brief Example

You can't get much simpler than the simplest `build.bfg` file:

```python
executable('simple', files=['simple.cpp'])
```

To build this executable, we need to create the actual build files and then
run them:

```sh
bfg9000 path/to/src/ build/
cd build
make
```

From there, you can run your newly-created executable: `./simple`. Hooray!

For further examples, please see the
[`examples/`](https://github.com/jimporter/bfg9000/tree/master/examples)
subdirectory.

## License

This project is licensed under the BSD 3-clause license.
