import sys
from setuptools import setup, Extension
import os
import warnings

PYPINAME = "mashing-pumpkins"
PACKAGENAME = "mashingpumpkins"
VERSION="0.3.0"

extra_compile_args = ['-pedantic']

CLASSIFIERS = [
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: C++",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Topic :: Scientific/Engineering",
]

if tuple(sys.version_info[:2]) < (3, 5):
    print("Error: Python >= 3.5 is *required*.")
    sys.exit(1)

if sys.platform == 'darwin':
    warnings.warn("Not tested on OSX. Feedback welcome.")
    pass
elif sys.platform == 'linux':
    pass
else:
    warnings.warn("The platform %s is not supported. "
                  "This may or may not work" % sys.platform)

mmh_mod = Extension("%s._murmurhash3" % PACKAGENAME,
                    sources=["src/_murmurhash3.cpp", "src/MurmurHash3.cpp"],
                    depends=["src/MurmurHash3.h"],
                    include_dirs=["src",],
                    language="c++",
                    extra_compile_args=(extra_compile_args+
                                        ['-O3']))

mmhmash_mod = Extension("%s._murmurhash3_mash" % PACKAGENAME,
                        sources=["src/_murmurhash3_mash.cpp",
                                 "src/MurmurHash3.cpp"],
                        depends=["src/MurmurHash3.h"],
                        include_dirs=["src",],
                        language="c++",
                        extra_compile_args=(extra_compile_args+
                                            ['-O3']))

xxh_mod = Extension("%s._xxhash" % PACKAGENAME,
                    sources=["src/_xxhash.c", "src/xxhash.c"],
                    depends=["src/xxhash.h"],
                    include_dirs=["src",],
                    language="c",
                    extra_compile_args = (
                        extra_compile_args +
                        ['-O3',
                         '-std=c99',
                         '-Wall', '-Wcast-qual',
                         '-Wcast-align', '-Wshadow',
                         '-Wstrict-aliasing=1', '-Wswitch-enum',
                         '-Wdeclaration-after-statement',
                         '-Wstrict-prototypes', '-Wundef'] +
                        ([] if sys.platform == 'windows' else ['-Wextra']))
                    )

setup(
    name=PYPINAME,
    version=VERSION,
    description="Hash sketches of sequences",
    license="MIT",
    author="Laurent Gautier",
    author_email="lgautier@gmail.com",
    url="https://github.com/lgautier/mashing-pumpkins",
    packages=[PACKAGENAME,
              PACKAGENAME + '.tests'],
    package_dir={PACKAGENAME: 'src'},
    ext_modules=[mmh_mod, mmhmash_mod, xxh_mod],
    requires=['setuptools'],
    extras_require={
        'test': ['pytest']},
    classifiers=CLASSIFIERS)
