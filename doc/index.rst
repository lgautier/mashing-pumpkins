.. mashing-pumpkins documentation master file, created by
   sphinx-quickstart on Mon Jan 23 15:17:43 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

mashing-pumpkins : m(in|ax)hash
===============================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

About
-----

This package is a library to perform top and bottom sketches, or min-hash / max-hash sketches for sequences
of bytes, using fixed-length subsets as the candidate components of the sketch.

The design of this package aims at making experimentations with such sketches easy to perform while
conserving a reasonable performance profile. At the time of writing it has a very competitive performance profile
both in runtime and memory usage when compared to alternatives.

Installation
------------

Released versions are on the Python package index (pypi) and can installed with
`pip`.

.. code-block:: bash

   pip install mashing-pumpkins


.. note::

   A C/C++ compiler as well the Python development headers will be required. The C compiler should accept
   the flag `-std=c99`.

.. warning:

   This was package was designed for Python 3.5, and is tested on both Python 3.5 and 3.6.
   Earlier versions of Python are not expected to work.
   

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


Composability
^^^^^^^^^^^^^

Top and bottom sketches have interesting composability properties, which we represent by letting them be "added"
to one another.

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


The methods are

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
and :class:`mashingpumpkins.minhashsketch.MinSketch.freeze` respectively) that returns a frozen set.


classes
^^^^^^^

.. autoclass:: mashingpumpkins.minhashsketch.MaxSketch
   :members:
   :exclude-members: add
		     
   .. automethod:: mashingpumpkins.minhashsketch.MaxSketch.add(seq, hashbuffer=array)

.. autoclass:: mashingpumpkins.minhashsketch.MinSketch
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

The expected benefit is too allow explorations in child classes or other additional structures while keeping the core
classes relatively lean.
      
.. autoclass:: mashingpumpkins.minhashsketch.MaxCountSketch
   :show-inheritance:
   :members:
   :undoc-members:
   :private-members:
   :special-members:
   :exclude-members: __module__

      
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
