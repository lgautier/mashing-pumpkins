from heapq import heappush, heapreplace
import operator
from collections import Counter
import array
from mashingpumpkins.sequence import chunkpos_iter


def make_elt(h, substr, j, nsize):
    ngram = substr[j:(j+nsize)]
    return (h, ngram)


def _minmaxhash_add_ngrams(
        heap: list, heapmap: dict, maxsize: int,
        nsize: int,
        subs, nsubs: int,
        hashbuffer, heaptop,
        extracthash,
        make_elt, update_elt,
        replace, anynew, minmax_op) -> int:
    """
    Process/add elements to the sketch (See warning below).

    This function is where most of time is spent when building a minhash or
    a maxhash.

    .. warning::

       If calling this method directly, updating the attribute
       `nvisited` is under your responsibility.

    :param heap: a heap (in a :class:`list`)
    :param heapmap: a :class:dict: with the content of the heap (for O(1)
        lookup of the content of the sketch)
    :param maxsize: maximum size of the heap
    :param nsize: size of ngrams
    :param subs: (sub-)sequence
    :param nsubs: number of hash values in the hashbuffer
    :param hashbuffer: buffer with hash values
    :param heaptop: hash value that is at the top of the heap
    :param extracthash: function extract the hash from an element
    :param make_elt: factory to make a new element
    :param update_elt: in-place update of an element
    :param replace: callback if replacing
    :param anynew: callback if new entry
    :param minmax_op: a pair that is expected to be either (1, `<`) if
        minhash or (-1, `>`) if maxhash.

    :return: new hash value for heaptop.
    """

    lheap = len(heap)
    sign, comparator = minmax_op

    for j in range(nsubs):
        h = hashbuffer[j]
        if h not in heapmap:
            if lheap < maxsize:
                elt = make_elt(sign * h, subs, j, nsize)
                # Add element to set and heap.
                heapmap[h] = elt
                heappush(heap, elt)

                heaptop = extracthash(heap[0])
                lheap += 1
                if anynew is not None:
                    anynew(h)
            elif comparator(h, heaptop):
                elt = make_elt(sign * h, subs, j, nsize)
                # Replace the maximum value in the heap.
                heapmap[h] = elt
                out = heapreplace(heap, elt)
                del (heapmap[sign * out[0]])
                # The negative of the hash is needed for MinHash.
                heaptop = sign * heap[0][0]
                if anynew is not None:
                    anynew(h)
        else:
            if update_elt is not None:
                elt = heapmap[h]
                update_elt(elt)
    return heaptop


class SetSketch(object):

    _anynew = None

    @property
    def maxsize(self):
        """ Maximum size for the sketch. """
        return self._maxsize

    @property
    def nsize(self):
        """ Size of the ngrams / kmers. """
        return self._nsize

    @property
    def seed(self):
        """ Seed for hashfun """
        return self._seed

    @property
    def nvisited(self):
        """ Number of items in the set "seen" (considered for inclusion)
        so far. """
        return self._nvisited

    def __init__(self, nsize: int,
                 maxsize: int,
                 hashfun,
                 seed: int,
                 heap: list = None,
                 nvisited: int = 0):
        """
        - nsize: size of the ngrams / kmers
        - maxsize: maximum size for the sketch
        - hashfun: function used for hashing
            `hashfun(byteslike) -> hash value`
        - heap: heapified list (if unsure about what it is, don't change
            the default)
        - nvisited: number of kmers visited so far
        """
        self._nsize = nsize
        self._maxsize = maxsize
        self._hashfun = hashfun
        self._seed = seed
        if heap is None:
            self._heap = list()
        else:
            self._heap = heap
        self._heapmap = dict(self._heap)
        self._nvisited = nvisited

    def __len__(self):
        """
        Return the number of elements in the sketch. See also the property
        'nvisited'.
        """
        return len(self._heap)

    def __contains__(self, elt):
        """
        Return whether a given element is in the sketch

        - elt: an object as returned by the method `make_elt(h, obj)`
        """
        return elt in self._heapmap

    def _add_elt_unsafe(self, h, elt):
        """
        Add an element.

        - h: hash value
        - elt: an object as returned by the method `make_elt(h, obj)`

        Note: This method does not check whether the element is satisfying
        any property (if MaxHash, that is all elements in the sketch
        are the `maxsize` elements with the highest hash values).
        """
        self._heapmap[h] = elt
        heappush(self._heap, elt)

    def _replace(self, h, elt):
        """
        insert/replace an element

        - h: a hash value
        - elt: an object as returned by the method `make_elt(h, obj)`
        """
        heapmap = self._heapmap
        heapmap[h] = elt
        out = heapreplace(self._heap, elt)
        del (heapmap[self._extracthash(out)])
        return out

    def __add__(self, obj):
        """
        Add two sketches such as to perserve the sketch property with
        hash values.
        """
        if self.nsize != obj.nsize:
            raise ValueError(
                'Only objects with the same `nsize` can be added '
                '(here %i and %i).'
                % (self.nsize, obj.nsize)
            )

        if self._hashfun != obj._hashfun:
            raise ValueError(
                'Only objects with the same hashfunction can be added.'
            )

        if self.seed != obj.seed:
            raise ValueError(
                'Only objects with the same seed can be added.'
            )

        res = type(self)(self.nsize, self.maxsize, self._hashfun, self.seed)
        res.update(self)
        res.update(obj)
        return res

    def __iadd__(self, obj):
        self.update(obj)

    def __iter__(self):
        """
        Return an iterator over the elements in the sketch.
        """
        return iter(sorted(self._heap))

    def add(self, seq, hashbuffer=array.array('Q', [0, ]*250)):
        """ Add all sub-sequences of length `self.nsize` found in the sequence
        "seq".

        - seq: a bytes-like sequence than can be sliced, and the slices
            be consummed by the function in the property `hashfun` (given to
            the constructor)
        - hashbuffer: a buffer array to store hash values during batch C calls

        """
        hashfun = self._hashfun
        seed = self._seed
        heap = self._heap
        nsize = self._nsize
        lseq = len(seq)

        w = len(hashbuffer)
        assert nsize <= w

        anynew = self._anynew
        make_elt = self._make_elt
        extracthash = self._extracthash
        lheap = len(heap)
        if lheap > 0:
            heaptop = extracthash(heap[0])
        else:
            heaptop = self._initheap

        for slice_beg, slice_end in chunkpos_iter(nsize, lseq, w):
            subs = seq[slice_beg:slice_end]  # safe: no out-of-bound in Python
            nsubs = hashfun(subs, nsize, hashbuffer, seed)
            heaptop = self._add(subs, nsubs, hashbuffer, heaptop,
                                extracthash, make_elt, self._replace, anynew)
            self._nvisited += nsubs

    def freeze(self):
        return FrozenSketch(self._heapmap, self.nsize,
                            self._hashfun,
                            seed=self.seed,
                            maxsize=self.maxsize,
                            nvisited=self.nvisited)


class MaxSketch(SetSketch):
    """
    Top sketch, which contains a sample of the input set constituted of
    the `maxsize` elements with the highest hash values.
    """

    _initheap = 0
    _make_elt = staticmethod(make_elt)
    _extracthash = staticmethod(operator.itemgetter(0))

    def add_hashvalues(self, values):
        """
        Add hash values while conserving the top sketch characteristic of
        the set.

        Note: The attribute `nvisited` is not incremented as this can
        be used to merge several stop sketch sets.

        - values: an iterable of hash values
        """
        make_elt = self._make_elt
        anynew = self._anynew
        extracthash = self._extracthash
        heap = self._heap
        heapmap = self._heapmap
        maxsize = self._maxsize
        lheap = len(heap)
        if lheap > 0:
            heaptop = extracthash(heap[0])
        else:
            heaptop = None
        for h in values:
            if lheap < maxsize:
                if h not in heapmap:
                    elt = make_elt(h, '', 0, 0)
                    self._add_elt_unsafe(h, elt)
                    heaptop = extracthash(heap[0])
                    lheap += 1
                if anynew is not None:
                    anynew(elt)
            elif h >= heaptop:
                if h not in heapmap:
                    elt = make_elt(h, '', 0, 0)
                    self._replace(h, elt)
                    heaptop = extracthash(heap[0])
                if anynew is not None:
                    anynew(elt)

    def _add(self, subs, nsubs, hashbuffer, heaptop,
             extracthash, make_elt, replace, anynew) -> int:
        """
        Process/add elements to the sketch.

        If calling this method directly, updating the attribute
        `nvisited` is under your responsibility.

        - subs: (sub-)sequence
        - nsubs: number of hash values in the hashbuffer
        - hashbuffer: buffer with hash values
        - heaptop: top of the heap
        - extracthash:
        - make_elt:
        - replace:
        - anynew:
        """

        return _minmaxhash_add_ngrams(
            self._heap, self._heapmap, self._maxsize,
            self._nsize,
            subs, nsubs,
            hashbuffer, heaptop,
            extracthash, make_elt, None, replace, anynew, (+1, operator.ge))

    def update(self, obj):
        """
        Update the sketch with elements from `obj` in place (
        use `__add__` instead to make a copy).

        - obj: An instance of class MaxSketch (or an instance of a child class)
        """

        if not isinstance(obj, MaxSketch):
            raise ValueError('Mismatching sketch type.')

        if hasattr(obj, "nsize") and self.nsize != obj.nsize:
            raise ValueError("Mismatching 'nsize' (have %i, update has %i)"
                             % (self.nsize, obj.nsize))

        if hasattr(obj, "_hashfun") and self._hashfun != obj._hashfun:
            raise ValueError(
                'Only objects with the same hashfunction can be added.'
            )

        if self.seed != obj.seed:
            raise ValueError(
                'Mismatching seed value. This has %i and the update has %i'
                % (self.seed, obj.seed)
            )

        extracthash = self._extracthash
        heap = self._heap
        lheap = len(heap)
        heapmap = self._heapmap
        maxsize = self._maxsize
        if lheap > 0:
            heaptop = extracthash(heap[0])
        else:
            heaptop = self._initheap

        for elt in obj:
            h = extracthash(elt)
            if lheap < maxsize:
                if h not in heapmap:
                    self._add_elt_unsafe(h, elt)
                    heaptop = extracthash(heap[0])
                    lheap += 1
                # no anynew: responsibility of child class
                # if anynew is not None:
                #     anynew(h)
            if h >= heaptop:
                if h not in heapmap:
                    self._replace(h, elt)
                    heaptop = extracthash(heap[0])
                # no anynew: responsibility of child class
                # if anynew is not None:
                #     anynew(h)

        self._nvisited += obj.nvisited


class MinSketch(SetSketch):
    """
    Bottom sketch, which contains a sample of the input set constituted of the
    `maxsize` elements with the lowest hash values.
    """

    _initheap = 0

    _make_elt = staticmethod(make_elt)
    _extracthash = staticmethod(lambda x: -x[0])

    def _replace(self, h, elt):
        """
        insert/replace an element

        - h: a hash value
        - elt: an object as returned by the method `make_elt(h, obj)`
        """
        heapmap = self._heapmap
        heapmap[h] = elt
        out = heapreplace(self._heap, elt)
        del (heapmap[self._extracthash(out)])
        return out

    def _add(self, subs, nsubs, hashbuffer, heaptop,
             extracthash, make_elt, replace, anynew) -> int:
        """
        Process/add elements to the sketch (See warning below).

        - subs: (sub-)sequence
        - nsubs: number of hash values in the hashbuffer
        - hashbuffer: buffer with hash values
        - heaptop: top of the heap
        - extracthash:
        - make_elt:
        - replace:
        - anynew:

        .. warning::

           If calling this method directly, updating the attribute
           `nvisited` is under your responsibility.

        """
        return _minmaxhash_add_ngrams(
            self._heap, self._heapmap, self._maxsize,
            self._nsize,
            subs, nsubs,
            hashbuffer, heaptop,
            extracthash, make_elt, None, replace, anynew,
            (-1, operator.le))

    def add_hashvalues(self, values):
        """
        Add hash values while conserving the bottom sketch characteristic of
        the set.

        Note: The attribute `nvisited` is not incremented as this can
        be used to merge several stop sketch sets.

        - values: an iterable of hash values
        """
        make_elt = self._make_elt
        anynew = self._anynew
        extracthash = self._extracthash
        heap = self._heap
        heapmap = self._heapmap
        maxsize = self._maxsize
        lheap = len(heap)
        if lheap > 0:
            heaptop = extracthash(heap[0])
        else:
            heaptop = None
        for h in values:
            if lheap < maxsize:
                if h not in heapmap:
                    elt = make_elt(-h, '', 0, 0)
                    self._add_elt_unsafe(h, elt)
                    heaptop = extracthash(heap[0])
                    lheap += 1
                if anynew is not None:
                    anynew(elt)
            elif h <= heaptop:
                if h not in heapmap:
                    elt = make_elt(-h, '', 0, 0)
                    self._replace(h, elt)
                    heaptop = extracthash(heap[0])
                if anynew is not None:
                    anynew(elt)

    def update(self, obj):
        """
        Update the sketch with elements from `obj` in place
        (use `__add__` instead to make a copy).

        - obj: a MinSketch (or instance of a child class)
        """

        if not isinstance(obj, MinSketch):
            raise ValueError('Mismatching sketch type.')

        if hasattr(obj, "nsize") and (self.nsize != obj.nsize):
            raise ValueError(
                'Mismatching `nsize` (have %i, update has %i)'
                % (self.nsize, obj.nsize)
            )

        if hasattr(obj, "_hashfun") and (self._hashfun != obj._hashfun):
            raise ValueError(
                'Only objects with the same hashfunction can be added.'
            )

        if self.seed != obj.seed:
            raise ValueError(
                'Mismatching seed value. This has %i and the update has %i'
                % (self.seed, obj.seed)
            )

        extracthash = self._extracthash
        heap = self._heap
        lheap = len(heap)
        heapmap = self._heapmap
        maxsize = self._maxsize
        if lheap > 0:
            heaptop = extracthash(heap[0])
        else:
            heaptop = self._initheap

        for elt in obj:
            h = extracthash(elt)
            if lheap < maxsize:
                if h not in heapmap:
                    self._add_elt_unsafe(h, elt)
                    heaptop = extracthash(heap[0])
                    lheap += 1
                # no anynew: responsibility of child class
                # if anynew is not None:
                #     anynew(h)
            if h <= heaptop:
                if h not in heapmap:
                    self._replace(h, elt)
                    heaptop = extracthash(heap[0])
                # no anynew: responsibility of child class
                # if anynew is not None:
                #     anynew(h)

        self._nvisited += obj.nvisited


class CountTrait(object):
    """
    Methods for sketches also counting the number of occurences of hash values
    in the input set / sequence.
    """

    def _replace(self, h, elt):
        out = super()._replace(h, elt)
        del (self._count[self._extracthash(out)])
        return out

    def _anynew(self, h):
        self._count[h] += 1

    def update(self, obj):
        """
        In addition to the parent class' method `update()`, this is ensuring
        that the counts are properly updated.
        """
        super().update(obj)
        count = self._count
        for k in self._heapmap:
            count[k] += obj._count[k]

    def freeze(self):
        return FrozenCountSketch(self._heapmap, self._count, self._nsize,
                                 self._hashfun,
                                 seed=self.seed,
                                 maxsize=self.maxsize,
                                 nvisited=self.nvisited)


class MaxCountSketch(MaxSketch, CountTrait):
    """
    Top sketch where the number of times a hash value was found is also stored.
    """

    def __init__(self, nsize: int, maxsize: int,
                 hashfun, seed: int,
                 heap: list = None,
                 count: Counter = None,
                 nvisited: int = 0):
        """
        - nsize: size of the ngrams / kmers
        - maxsize: maximum size for the sketch
        - hashfun: function used for hashing
            `hashfun(byteslike) -> hash value`
        - seed: a seed for hashfun
        - heap: heapified list (if unsure about what it is, don't change
            the default)
        - count: a collections.Counter
        - nvisited: number of kmers visited so far
        """
        super().__init__(nsize, maxsize, hashfun, seed,
                         heap=heap, nvisited=nvisited)
        if count is None:
            count = Counter()
            if heap is not None:
                for elt in heap:
                    h = self._extracthash(elt)
                    if h in count:
                        raise ValueError(
                            'Elements in the heap must be unique.'
                        )
                    else:
                        count[h] = 1
        else:
            if len(set(self._heapmap) ^ set(count.keys())) > 0:
                raise ValueError(
                    'Mismatching keys with the parameter `count`.'
                )
        self._count = count


# TODO: code duplication with MaxCountSketch - may be using __new__()
# would solve this.
class MinCountSketch(MinSketch, CountTrait):
    """
    Top sketch where the number of times a hash value was found is also stored.
    """

    def __init__(self, nsize: int, maxsize: int,
                 hashfun, seed: int,
                 heap: list = None,
                 count: Counter = None,
                 nvisited: int = 0):
        """
        - nsize: size of the ngrams / kmers
        - maxsize: maximum size for the sketch
        - hashfun: function used for hashing
            `hashfun(byteslike) -> hash value`
        - seed: a seed for hashfun
        - heap: heapified list (if unsure about what it is, don't change
            the default)
        - count: a collections.Counter
        - nvisited: number of kmers visited so far
        """
        super().__init__(nsize, maxsize, hashfun, seed,
                         heap=heap, nvisited=nvisited)
        if count is None:
            count = Counter()
            if heap is not None:
                for elt in heap:
                    h = self._extracthash(elt)
                    if h in count:
                        raise ValueError(
                            'Elements in the heap must be unique.'
                        )
                    else:
                        count[h] = 1
        else:
            if len(set(self._heapmap) ^ set(count.keys())) > 0:
                raise ValueError(
                    'Mismatching keys with the parameter `count`.')
        self._count = count


class FrozenSketch(object):
    """
    Read-only sketch.
    """

    __slots__ = ('_sketch', '_nsize', '_hashfun', '_seed',
                 '_maxsize', '_nvisited')

    def __init__(self, sketch: set, nsize: int, hashfun=hash,
                 seed: int = None,
                 maxsize: int = None, nvisited: int = None):
        """
        Create an instance from:
        - sketch: a set
        - nsize: a kmer/ngram size
        - hashfun: a hashing function
        - seed: an optional seed for hashfun
        - maxsize: a maximum size for the input set (if missing, this is
          assumed to be len(setobj)
        - nvisited: the number of kmers/ngrams visited to create setobj
        """

        if maxsize is None:
            maxsize = len(sketch)
        elif maxsize < len(sketch):
            raise ValueError("The maximum size cannot be smaller than the "
                             "number of objects in the set.")
        if nvisited is None:
            nvisited = len(sketch)
        elif nvisited < len(sketch):
            raise ValueError("'nvisited' cannot be smaller than the number of "
                             "objects in the set.")

        self._sketch = frozenset(sketch)
        self._nsize = nsize
        self._hashfun = hashfun
        self._seed = seed
        self._maxsize = maxsize
        self._nvisited = nvisited

    @property
    def maxsize(self):
        """ Maximum size for the sketch. """
        return self._maxsize

    @property
    def nsize(self):
        """ Size of the ngrams / kmers. """
        return self._nsize

    @property
    def nvisited(self):
        """ Number of ngrams / kmers visited (considered for inclusion)
        so far. """
        return self._nvisited

    def jaccard_similarity(self, obj):
        """ Compute the Jaccard similarity index between this sketch and
        an other sketch"""
        return (
            len(self._sketch.intersection(obj._sketch)) /
            len(self._sketch.union(obj._sketch))
        )

    # Alias for `jaccard_similarity`
    jaccard_correspondance = jaccard_similarity

    def jaccard_containment(self, obj):
        """ Compute the Jaccard containment index between this sketch and
        an other sketch"""
        return (
            len(self._sketch.intersection(obj._sketch)) /
            len(self._sketch)
        )

    def dice_similarity(self, obj):
        """
        Soerensen-Dice similarity index as:
        DSC = 2q / (2q + r + s)
        """
        q = len(self._sketch.intersection(obj._sketch))
        r = len(self._sketch.difference(obj._sketch))
        s = len(obj._sketch.difference(self._sketch))
        return 2*q / (2*q + r + s)

    def __len__(self):
        """ Return the number of elements in the set. """
        return len(self._sketch)


class FrozenCountSketch(FrozenSketch):

    __slots__ = '_count'

    def __init__(self, sketch: set, count: Counter, nsize: int,
                 hashfun=hash, seed: int = None,
                 maxsize: int = None, nvisited: int = None):
        """
        Create an instance from:
        - sketch: a set
        - count: a counter
        - nsize: a kmer/ngram size
        - hashfun: a hashing function
        - seed: an optional seed for hashfun
        - maxsize: a maximum size for the input set (if missing, this is
          assumed to be len(setobj)
        - nvisited: the number of kmers/ngrams visited to create setobj
        """

        super().__init__(sketch, nsize, hashfun=hashfun, seed=seed,
                         maxsize=maxsize, nvisited=nvisited)
        self._count = count.copy()

    def bray_curtis_dissimilarity(self, obj):
        """
        Return the Bray-Curtis dissimilarity between this and an other
        FrozenCountSketch.
        """
        C_ij = sum(self._count[h]
                   for h in self._sketch.intersection(obj._sketch))
        S_i = sum(self._count)
        S_j = sum(obj._count)
        return 1 - (2 * C_ij) / (S_i + S_j)
