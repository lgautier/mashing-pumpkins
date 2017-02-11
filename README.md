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

## Why Minhash sketches ?

Bottom-sketches (Minhash sketches) are samples of the elements present in a set. In the context of genomics, this can mean
the k-mers present in a genome, or in the reads from a sequencing assay, and they have been shown to be useful to measure similarity
between genomes[1].

Sampling subsequences from genome sequences or sequence assays has also been demonstrated
to be a very efficient approach to identify DNA sequences of unknown origin[2], both in terms of accuracy and in
terms of usage of bandwidth.

This is making such sketches interesting tools for the analysis of NGS data, with several implementations already available[1,3]

1. [MASH](https://github.com/marbl/Mash) - Mash: fast genome and metagenome distance estimation using MinHash. Ondov BD, Treangen TJ, Melsted P, Mallonee AB, Bergman NH, Koren S, Phillippy AM. Genome Biol. 2016 Jun 20;17(1):132. doi: 10.1186/s13059-016-0997-x.
2. [Tapir/DNAsnout](https://bitbucket.org/lgautier/dnasnout-client) - Gautier, Laurent, and Ole Lund. "Low-bandwidth and non-compute intensive remote identification of microbes from raw sequencing reads." PloS one 8.12 (2013): e83784.(http://dx.doi.org/10.1371/journal.pone.0083784)
3. [sourmash](https://github.com/dib-lab/sourmash)


- MurmurHash3 code is in the public domain (author: Austin Appleby)
- XXHash code is released under BSD-2 license (author: Yann Collet)

## Why this implementation ?

The purpose of this implementation is to provide a library design that is combining flexibility and expressivity with performance
(speed and memory usage).

### Design

The design is allowing us to implement with a relatively short code base:

- the use different hash functions (MurmurHash3, XXHash), and with user-specified seeds
- Minhash and Maxhash sketches
- "Count sketches"
- Demonstrate quickly the comparative efficiency of alternative hashing strategies for double-stranded genomes (see - https://github.com/marbl/Mash/issues/45#issuecomment-274665746)

### Performance

The implementation also happens to be pretty fast, making it a reasonable option as a building block for minhash-related research and prototypes.
At the time of writing it is able to build a minhash sketch (k=31, size=1000) for a FASTQ file with ~21M reads (700MB when gzip-compressed)
on a laptop[*] in under 1'30".

```bash
$ python -m mashingpumpkins.demo.cmdline --parser=fastqandfurious --ncpu=3 DRR065801.fastq.gz
Processing DRR065801.fastq.gz as a FASTQ file...
    20853697 records in 1m20s (9.43 MB/s)
```

(*: ASUS ultrabook, dual-core with hyperthreading, running Linux)

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

While this is primarily a Python libray, a demo command line it available
(**note: this requires the Python package `sourmash` (its dev version in `master`)**):

```bash

python -m mashingpumpkins.demo.cmdline

```


### Misc.

```
Q: Why Python 3-only ?
A: Because I am coming from the __future__ ...
```
