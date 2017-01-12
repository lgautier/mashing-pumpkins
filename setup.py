import sys
from distutils.core import setup, Extension
import os
import warnings

PACKAGENAME = "mashingpumpkins"
VERSION="0.1"

EXTRA_COMPILE = ['-pedantic']

CLASSIFIERS = [
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: C++",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Topic :: Scientific/Engineering",
]

if sys.platform == 'darwin':
    warnings.warn("Not tested on OSX")
    pass
elif sys.platform == 'linux':
    pass
else:
    raise ValueError("The platform %s is not supported." % sys.platform)

mmh_mod = Extension("%s._murmurhash3" % PACKAGENAME,
                    sources=["src/_murmurhash3.cpp", "src/MurmurHash3.cpp"],
                    include_dirs=["src",],
                    language="c++")
xxh_mod = Extension("%s._xxhash" % PACKAGENAME,
                    sources=["src/_xxhash.c", "src/xxhash.c"],
                    include_dirs=["src",],
                    language="c")

setup(
    name = PACKAGENAME,
    version = VERSION,
    description = "Hash sketches of sequences",
    license = "MIT",
    author = "Laurent Gautier",
    email = "lgautier@gmail.com",
    packages = [PACKAGENAME],
    package_dir = {PACKAGENAME: 'src'},
    ext_modules = [mmh_mod, xxh_mod],
    classifiers = CLASSIFIERS)



