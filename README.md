# bfg9000 - build file generator

[![Travis build status][travis-image]][travis-link]
[![Appveyor build status][appveyor-image]][appveyor-link]
[![Documentation][documentation-image]][documentation-link]

**bfg9000** is a cross-platform *build configuration system* with an emphasis on
making it easy to define how to build your software. It converts a Python-based
build script into the appropriate files for your underlying build system of
choice (Ninja, Make, or MSBuild).

## A brief example

You can't get much simpler than the simplest `build.bfg` file:

```python
executable('simple', files=['simple.cpp'])
```

To build this executable, we need to create the actual build files and then
run them:

```sh
bfg9000 path/to/src/ build/
cd build
ninja
```

From there, you can run your newly-created executable: `./simple`. Hooray!

For further examples, please see the
[`examples/`](https://github.com/jimporter/bfg9000/tree/master/examples)
subdirectory.

# Installation

bfg9000 uses [setuptools](http://pythonhosted.org/setuptools/), so installation
is much the same as any other Python package. Just run:

```sh
python setup.py install
```

From there, you can start using bfg to build your software!

## License

This project is licensed under the BSD 3-clause license.

[travis-image]: https://travis-ci.org/jimporter/bfg9000.svg?branch=master
[travis-link]: https://travis-ci.org/jimporter/bfg9000
[appveyor-image]: https://ci.appveyor.com/api/projects/status/hxvbggf6exq8i2k6/branch/master?svg=true
[appveyor-link]: https://ci.appveyor.com/project/jimporter/bfg9000/branch/master
[documentation-image]: https://img.shields.io/badge/docs-bfg9000-blue.svg
[documentation-link]: http://jimporter.github.io/bfg9000/
