[![logo](doc/_static/mashingpumpkins.png)](doc/_static/mashingpumpkins.png)
# mashing-pumpkins

Flexible-yet-pretty-fast minhashing-related library for Python >= 3.5.

[![Build Status](https://travis-ci.org/lgautier/mashing-pumpkins.svg?branch=master)](https://travis-ci.org/lgautier/mashing-pumpkins)
[![codecov](https://codecov.io/gh/lgautier/mashing-pumpkins/branch/master/graph/badge.svg)](https://codecov.io/gh/lgautier/mashing-pumpkins)
[![Pypi release](https://img.shields.io/pypi/v/mashing-pumpkins.svg)](https://img.shields.io/pypi/v/mashing-pumpkins.svg)

The package is rather well documented with:
- Sphinx documentation in [doc/](doc/) (start with [doc/index.rst](doc/index.rst))
- Docstrings for most of the functions, classes, and methods
- A showcase notebook in [doc/notebooks](doc/notebooks)
- A demo command-line tool to build sketches in sourmash's JSON format (`python -m mashingpumpkins.demo.cmdline --help`)

Why Minhash sketches ?

- [MASH](https://github.com/marbl/Mash) (Mash: fast genome and metagenome distance estimation using MinHash. Ondov BD, Treangen TJ, Melsted P, Mallonee AB, Bergman NH, Koren S, Phillippy AM. Genome Biol. 2016 Jun 20;17(1):132. doi: 10.1186/s13059-016-0997-x.)
- [sourmash](https://github.com/dib-lab/sourmash)


- MurmurHash3 code is in the public domain (author: Austin Appleby)
- XXHash code is released under BSD-2 license (author: Yann Collet)


## Installation

Python 3.5 or 3.6 and a C/C++ compiler (C99-aware) are pretty much everything that is needed. At the time of writing the CI
on Travis is testing with gcc and clang.

With pip, installing either latest release or the "master" branch can be done with:

```bash
# latest release
pip install mashing-pumpkins

# master on github
pip install git+https://https://github.com/lgautier/mashing-pumpkins.git

```

The installation can be tested with:

```bash
python -m pytest --pyargs mashingpumpkins

# or:

python -m pytest --cov=mashingpumpkins ---cov-report term
```

## Usage

This is primarily a Python libray, but at the time writing we are a little demo section going on
(**note: this requires the Python package `sourmash` (its dev version in `master`)**):

```bash

python -m mashingpumpkins.demo.cmdline

```


### Misc.

```
Q: Why Python 3-only ?
A: Because I am coming from the __future__ ...
```
