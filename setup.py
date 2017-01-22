import sys
from distutils.core import setup, Extension
import os
import warnings

PACKAGENAME = "mashingpumpkins"
VERSION="0.1"

extra_compile_args = ['-pedantic']

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
                    language="c++",
                    extra_compile_args = extra_compile_args + \
                    ['-O3'])                    

mmhmash_mod = Extension("%s._murmurhash3_mash" % PACKAGENAME,
                        sources=["src/_murmurhash3_mash.cpp", "src/MurmurHash3.cpp"],
                        include_dirs=["src",],
                        language="c++",
                        extra_compile_args = extra_compile_args + \
                        ['-O3'])                    

xxh_mod = Extension("%s._xxhash" % PACKAGENAME,
                    sources=["src/_xxhash.c", "src/xxhash.c"],
                    include_dirs=["src",],
                    language="c",
                    extra_compile_args = extra_compile_args + \
                    ['-O3',
                     '-std=c99',
                     '-Wall', '-Wextra', '-Wcast-qual', '-Wcast-align', '-Wshadow',
                     '-Wstrict-aliasing=1', '-Wswitch-enum', '-Wdeclaration-after-statement',
                     '-Wstrict-prototypes', '-Wundef'])

setup(
    name = PACKAGENAME,
    version = VERSION,
    description = "Hash sketches of sequences",
    license = "MIT",
    author = "Laurent Gautier",
    author_email = "lgautier@gmail.com",
    packages = [PACKAGENAME,
                PACKAGENAME + '.tests',
                PACKAGENAME + '.demo'],
    package_dir = {PACKAGENAME: 'src'},
    ext_modules = [mmh_mod, mmhmash_mod, xxh_mod],
    extras_require = {
        'test' : ['sourmash'],
        'demo' : ['sourmash']},
    classifiers = CLASSIFIERS)



