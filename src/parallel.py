"""
Parallelization utilities
"""

from mashingpumpkins.sequence import chunkpos_iter
from functools import reduce
import multiprocessing

class Sketch(object):

    @staticmethod
    def initializer(cls, *args):
        """
        FIXME: use of global not really nice (possible root of mysterious issue for user)
        """
        global sketch_constructor
        def sketch_constructor():
            return cls(*args)

    
    @staticmethod
    def map_sequence(sequence):
        """
        - sequence: a bytes-like object

        return: a sketch
        """
        mhs = sketch_constructor()
        mhs.add(sequence)
        return mhs

    @staticmethod
    def map_sequences(iterable):
        """
        - iterable: an iterable of bytes-like objects

        return: a sketch
        """
        mhs = sketch_constructor()
        for sequence in iterable:
            mhs.add(sequence)
        return mhs

    @staticmethod
    def reduce(a, b):
        """
        Update the sketch a with the content of sketch b.

        - a: a sketch
        - b: a sketch

        return a.update(b)
        """
        a.update(b)
        return a

