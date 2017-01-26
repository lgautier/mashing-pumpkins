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


class SketchList(object):

    @staticmethod
    def initializer(clslist, argslist):
        """
        FIXME: use of global not really nice (possible root of mysterious issue for user)
        """

        # Allow automagic expansion of the list of classes
        if len(clslist) == 1:
            clslist = tuple(clslist[0] for x in range(len(argslist)))

        # Allow automagic expansion of the list of args
        if len(argslist) == 1:
            argslist = tuple(argslist[0] for x in range(len(clslist)))
        
        if len(clslist) != len(argslist):
            raise ValueError("The arguments argslist and clslist must be sequences of either the "
                             "same length, or of length 1.")
        
        global sketchlist_constructor
        def sketchlist_constructor():
            return (cls(*args) for cls, args in zip(clslist, argslist))

    
    @staticmethod
    def map_sequence(sequence):
        """
        - sequence: a bytes-like object

        return: a sketch
        """
        mhslist = tuple(sketchlist_constructor())
        for mhs in mhslist:
            mhs.add(sequence)
        return mhslist

    @staticmethod
    def map_sequences(iterable):
        """
        - iterable: an iterable of bytes-like objects

        return: a sketch
        """
        mhslist = sketchlist_constructor()
        for sequence in iterable:
            for mhs in mhslist:
                mhs.add(sequence)
        return mhs

    @staticmethod
    def reduce(alist, blist):
        """
        Update the sketch a with the content of sketch b.

        - alist: a sequence of sketches
        - blist: a sequence of sketches

        return alist after each of its elements has been updated to the corresponding element in blist
        """
        for a,b in zip(alist, blist):
            a.update(b)
        return alist

