# Contributing

So, you'd like to help improve bfg9000 by writing a patch? Great! This page will
provide you with some useful information to help you get started.

## Running tests

bfg9000 has a suite of tests to ensure that everything works properly. (Well,
everything that has tests!) As you may expect, you can run these via:

```sh
$ python setup.py test
```

If you'd like to run a subset of tests, such as when trying to fix a bug in a
specific area of the code, you can limit the tests that get run. For instance,
to run only the tests in `test/integration/test_simple.py`, you can type:

```sh
$ python setup.py test -s test.integration.test_simple
```

## Linting code

bfg9000 uses [flake8](https://flake8.readthedocs.org/en/latest/) for linting.
Since users generally don't need to worry about linting the codebase, this isn't
automatically installed by setup.py. You'll need to install it yourself. Once
installed, you can use the `lint` command like so:

```sh
$ python setup.py lint
```
