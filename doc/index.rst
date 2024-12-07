.. mashing-pumpkins documentation master file, created by
   sphinx-quickstart on Mon Jan 23 15:17:43 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

mashing-pumpkins : m(in|ax)hash
===============================

Flexible-yet-pretty-fast minhash/maxhash-related library for Python > 3.8.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. image:: https://travis-ci.org/lgautier/mashing-pumpkins.svg?branch=master
    :target: https://travis-ci.org/lgautier/mashing-pumpkins

.. image:: https://img.shields.io/pypi/v/mashing-pumpkins.svg
    :target: https://img.shields.io/pypi/v/mashing-pumpkins.svg


About
-----

This package is a library to perform top and bottom sketches, or MinHash /
MaxHash sketches initially for sequences of bytes, using fixed-length
subsets as the candidate components of the sketch (also called
"k-minimum values" variant of MinHash).

The design of this package aims at making experimentations with such sketches
easy to perform while conserving a reasonable performance profile. At the time
of writing it has a very competitive performance profile both in runtime and
memory usage when compared to alternatives.


Why Minhash sketches ?
^^^^^^^^^^^^^^^^^^^^^^

Bottom-sketches (Minhash sketches) are samples of the elements present in a set.
They have been extensively used for text document matching or retrieval, which can
extend to the context of genomics where strings are DNA or RNA sequences. There the
set of k-mers present in a genome (called "k-shingles" in MinHash-related litterature),
or in the reads from a sequencing assay, and they have been shown to be useful to
measure similarity between genomes[1].

Sampling subsequences from genome sequences or sequence assays has also been
demonstrated to be a very efficient approach to identify DNA sequences of unknown
origin[2], both in terms of accuracy and in terms of usage of bandwidth.

This is making such sketches interesting tools for the analysis of NGS data, with several
implementations already available[1,3]

1. `MASH`_ (Mash: fast genome and metagenome distance estimation using MinHash. Ondov BD,
   Treangen TJ, Melsted P, Mallonee AB, Bergman NH, Koren S, Phillippy AM. Genome Biol. 2016
   Jun 20;17(1):132. doi: 10.1186/s13059-016-0997-x.)
2. `Tapir/DNAsnout`_ ([Gautier, Laurent, and Ole Lund. "Low-bandwidth and non-compute
   intensive remote identification of microbes from raw sequencing reads." PloS one 8.12
   (2013): e83784.](http://dx.doi.org/10.1371/journal.pone.0083784))
3. `sourmash`_

.. _MASH: https://github.com/marbl/Mash
.. _Tapir/DNAsnout: https://bitbucket.org/lgautier/dnasnout-client
.. _sourmash: https://github.com/dib-lab/sourmash


Why this implementation ?
^^^^^^^^^^^^^^^^^^^^^^^^^

The purpose of this implementation is to provide a library design that is combining flexibility and expressivity with performance
(speed and memory usage).


Design
""""""

The design is allowing us to implement with a relatively short code base:

- the use different hash functions (MurmurHash3, XXHash), and with user-specified seeds
- Minhash and Maxhash sketches
- "Count sketches"
- Demonstrate quickly the comparative efficiency of alternative hashing strategies for double-stranded genomes (see - https://github.com/marbl/Mash/issues/45#issuecomment-274665746)

Performance
"""""""""""

The implementation also happens to be pretty fast, making it a reasonable option as a building block for minhash-related research and prototypes.
At the time of writing it is able to build a minhash sketch (k=31, size=1000) for a FASTQ file with ~21M reads (700MB when gzip-compressed)
on a laptop[1] in under 1'30".

.. code-block:: bash

   $ python -m mashingpumpkins.demo.cmdline --parser=fastqandfurious --ncpu=3 DRR065801.fastq.gz
   Processing DRR065801.fastq.gz as a FASTQ file...
       20853697 records in 1m20s (9.43 MB/s)


1. ASUS ultrabook, dual-core with hyperthreading, running Linux - adding more cores to the task on more powerful hardware should make it faster


Installation
------------

The package released under an MIT license. It contains code for the following hashing functions:

- MurmurHash3 (public domain - author: Austin Appleby)
- XXHash (BSD-2 license - author: Yann Collet)


Released versions are on the Python package index (pypi) and can installed with
`pip`.

.. code-block:: bash

   pip install mashing-pumpkins


To install the master on github:

.. code-block:: bash

   # master on github
   pip install git+https://https://github.com/lgautier/mashing-pumpkins.git

   
.. note::

   A C/C++ compiler as well the Python development headers will be required. The C compiler should accept
   the flag `-std=c99`.

.. warning:

   This was package was designed for Python 3.5, and is tested on both Python 3.5 and 3.6.
   Earlier versions of Python are not expected to work.
   
The installation can be tested with:

.. code-block:: bash

   python -m pytest --pyargs mashingpumpkins


or:

.. code-block:: bash

   python -m pytest --cov=mashingpumpkins ---cov-report term



Usage
-----

Jupyter notebooks are available in the `doc/notebooks`_ (in the source tree).

.. _doc/notebooks: https://github.com/lgautier/mashing-pumpkins/tree/master/doc/notebooks

While this is primarily a Python libray, there is also demo command line:

.. code-block:: bash

   python -m mashingpumpkins.demo.cmdline


.. note::

   This requires the Python package :mod:`sourmash` (its dev version in `master`)

   
Sketches
--------

A bottom-sketch of maximum size `maxsize` is a sample of the elements in a set such as only the `maxsize` smallest hash values
for all elements are selected (or `maxsize` highest hash values if a top sketch). Here the elements are the sub-sequences of
length `nsize` in one or a collection of input sequences.

For example, building a bottom sketch just as done by MASH and sourmash can be written in few lines:

.. code-block:: python

   # import parts needed
   from mashingpumpkins.minhashsketch import MinSketch
   from mashingpumpkins.sourmash import mash_hashfun, DEFAULT_SEED

   # create a min-sketch
   nsize = 31
   maxsize = 1000
   mhs = MinSketch(nsize,
                   maxsize,
                   mash_hashfun,
                   DEFAULT_SEED)

   # add a sequence 
   sequence_a = b'AATACCAAGACAGAGACAGACCCAGACAGATGACGAT'
   mhs.add(sequence_a)

   # add an other sequence 
   sequence_b = b'TTAGCGTAGGGTGCCGATAGGGATAGGGACCCGAATGGGAGGAGAAAAG'
   mhs.add(sequence_b)

If after a top-sketch, there is a class for this.

.. code-block:: python

   # import parts needed
   from mashingpumpkins.minhashsketch import MaxSketch


Sketches of arbritary objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

While the library was designed to work on sequences of bytes for which
sketches are the MinHash or MaxHash sets for all k-shingles of fixed
window length, it can also work with input sets of arbitrary objects,
although this requires to defined adapter hashing functions
ignore parameters associated with windowing, and if the hashing
function returns a non-numerical only use :class:`MaxSketch`.

.. code-block:: python

    import hashlib
    mhs = (mashingpumpkins.minhashsketch
           .MaxSketch(
               None,  # size is unspecified
               maxsize,
               None,  # hashing function
               None  # seed
           )
          )

     x = object()
     mhs.add_hashvalues([x])

An other example is when all elements in the input set are :class:`bytes` and
the common hashing function SHA1 is wanted. In that case the hashing function
would look like follows. Note that hashing function can return non-numerical
values and the hashing function will plainly ignore parameters `size` and
`buffer` as no sliding window is wanted.

.. code-block:: python

    def hashing_sha1(obj, size, buffer=None, seed=None):
        return (hashlib.sha1(obj).digest(), )

    import hashlib
    mhs = (mashingpumpkins.minhashsketch
           .MaxSketch(
               None,  # size is unspecified
               maxsize,
               None,
               None  # seed
           )
          )

    values = (hashlib.sha1(x).digest()
              for x in (b'This is a sequence of bytes',
                        b'This is an other sequence of bytes'))
    mhs.add_hashvalues(values)



Composability
^^^^^^^^^^^^^

Top and bottom sketches have interesting composability properties, which we represent by letting them be "added"
to one another. That property can be useful for parallelization (See :ref:`parallel`).

.. code-block:: python

   # sketch for sequencea
   mhs_a = MinSketch(nsize,
                     maxsize,
                     mash_hashfun,
                     DEFAULT_SEED)

   mhs_a.add(sequence_a)

   # sketch for sequence_a
   mhs_b = MinSketch(nsize,
                     maxsize,
                     mash_hashfun,
                     DEFAULT_SEED)

   mhs_a.add(sequence_b)

   # "add" the two sketches
   mhs_ab = mhs_a + mhs_b

   # remember our `mhs` above to which sequence_a and sequence_b
   # where added ? mhs_ab contains the same sketch.


The methods are:

- :meth:`mashingpumpkins.minhashsketch.MaxSketch.__add__`
- :meth:`mashingpumpkins.minhashsketch.MaxSketch.__iadd__`
- :meth:`mashingpumpkins.minhashsketch.MaxSketch.update`
- :meth:`mashingpumpkins.minhashsketch.MinSketch.__add__`
- :meth:`mashingpumpkins.minhashsketch.MinSketch.__iadd__`
- :meth:`mashingpumpkins.minhashsketch.MinSketch.update`


Freezing
^^^^^^^^

The classes :class:`mashingpumpkins.minhashsketch.MaxSketch` and :class:`mashingpumpkins.minhashsketch.MinSketch`
are designed to build sketches, and to do so efficiently they contain data structures than may be not be necessary for further
use. To highlight this usage pattern we have a method `freeze` (:meth:`mashingpumpkins.minhashsketch.MaxSketch.freeze`
and :class:`mashingpumpkins.minhashsketch.MinSketch.freeze` respectively) that returns an instance of a
class wrapping :class:`frozenset`.

"Frozen" sets have methods to compute similarity measure (e.g., two Jaccard's index measures - see the class
:class:`mashingpumpkins.minhashsketch.FrozenSketch` for a full list).

classes
^^^^^^^

.. autoclass:: mashingpumpkins.minhashsketch.MaxSketch
   :members:
   :exclude-members: add
		     
   .. automethod:: mashingpumpkins.minhashsketch.MaxSketch.add(seq, hashbuffer=array)

.. autoclass:: mashingpumpkins.minhashsketch.MinSketch
   :members:


.. autoclass:: mashingpumpkins.minhashsketch.FrozenSketch
   :members:


Hashing functions
-----------------

The package first entry point to customization is to allow the use of different hashing function. Several proposed
hashing function are included, but any Python function satisfying the required interface can be used.


Hashing functions included
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: mashingpumpkins.sourmash.mash_hashfun(sequence, nsize, buffer)

.. automodule:: mashingpumpkins._murmurhash3
   :members:

.. automodule:: mashingpumpkins._murmurhash3_mash
   :members:

.. automodule:: mashingpumpkins._xxhash
   :members:


Extending the base classes
--------------------------

The sketch is a set of hash values. This means that each hash value is represented only once.
However, it might be intersting to count the number of times a hash value is seen in the input data.
This can be achieved relatively easily by extending one of the base sketch classes. More
precisely, by overriding the methods :meth:`__init__`, :meth:`_anynew`, :meth:`_replace`, :meth:`freeze`, and :meth:`update`.
Each one of these method contain very little code, and the design made to allow this function to only implement
additional operations (the methods call the parent class' method, and the added part concern the update of a
:class:`collections.Counter` to keep track of the number of times a hash values has been seen so far).

The handling of counting is gathered in the class :class:`mashingpumpkins.minhashsketch.CountTrait` and is used
by :class:`mashingpumpkins.minhashsketch.MaxCountSketch` and :class:`mashingpumpkins.minhashsketch.MinCountSketch`.
      

The expected benefit is too allow exploration in child classes or other additional structures while keeping the core
classes relatively lean.


.. autoclass:: mashingpumpkins.minhashsketch.CountTrait
   :show-inheritance:
   :members:
   :undoc-members:
   :private-members:
   :special-members:
   :exclude-members: __module__, __dict__, __weakref__

.. autoclass:: mashingpumpkins.minhashsketch.SetSketch
   :show-inheritance:
   :members:
   :undoc-members:
   :private-members:
   :special-members:
   :exclude-members: __module__

.. autoclass:: mashingpumpkins.minhashsketch.MaxCountSketch
   :show-inheritance:
   :members:
   :undoc-members:
   :private-members:
   :special-members:
   :exclude-members: __module__
		     
.. autoclass:: mashingpumpkins.minhashsketch.MinCountSketch
   :show-inheritance:
   :members:
   :undoc-members:
   :private-members:
   :special-members:
   :exclude-members: __module__

.. _parallel:
      
Parallelization utilities
-------------------------

This module suggests primitives to write code performing parallel computation.

For example using :mod:`multiprocessing` to build in parallel a sketch
for a list of large sequences (e.g., the chromosomes in a genome):

.. code-block:: python

   import multiprocessing
   from mashingpumpkins.minhashsketch import MinSketch
   from mashingpumpkins.sourmash import mash_hashfun, DEFAULT_SEED
   from mashingpumpkins import parallel

   ncpu = 4
   
   ksize = 31
   maxsize = 1000
   # create child processes
   p = multiprocessing.Pool(ncpu,
                            initializer=parallel.Sketch.initializer,
                            initargs=(MinSketch, ksize, maxsize,
                                      mash_hashfun, DEFAULT_SEED))
   # map the list of sequences
   result = p.imap_unordered(Sketch.map_sequence,
                             sequences)
   # reduce into a result sketch
   mhs = reduce(Sketch.reduce, result,
                MinHash(ksize, maxsize, mash_hashfun, DEFAULT_SEED))
   # finalize the child processes
   p.finalize()

   
.. automodule:: mashingpumpkins.parallel
   :members:

Misc. utilities
---------------

.. automodule:: mashingpumpkins.sequence
   :members:

	     

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
