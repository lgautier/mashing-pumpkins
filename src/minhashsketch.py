from heapq import heappush, heapreplace
from collections import Counter
import array

class MaxHashNgramSketch(object):
    """
    MaxHash Sketch.
    """

    _anynew = None
    
    def __init__(self, nsize: int,
                 maxsize: int,
                 hashfun,
                 heap : list = None,
                 nvisited: int = 0):
        """
        - nsize: size of the ngrams / kmers
        - maxsize: maximum size for the sketch
        - hashfun: function used for hashing - `hashfun(byteslike) -> hash value`
        - heap: heapified list (if unsure about what it is, don't change the default)
        - nvisited: number of kmers visited so far
        """
        self._nsize = nsize
        self._maxsize = maxsize
        self._hashfun = hashfun
        if heap is None:
            self._heap = list()
        else:
            self._heap = heap
        self._heapset = set(self._heap)
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
        """ Number of ngrams / kmers visited (considered for inclusion) so far. """
        return self._nvisited

    def _add(self, elt):
        """ 
        Add an element.

        - elt: an object as returned by the method `make_elt()` 

        Note: This method does not check whether the element is satisfying
        the MaxHash property,        
        """
        self._heapset.add(elt)
        heappush(self._heap, elt)

    def _replace(self, elt):
        heapset = self._heapset
        heapset.add(elt)
        out = heapreplace(self._heap, elt)
        heapset.remove(out)
        return out

    def _make_elt(self, h, ngram):
        """
        Make an element to store into the sketch
        
        - h: an hash value
        - ngram: the object (ngram/kmer) at the source of the hash value
        """
        return (h, bytes(ngram))

    def __len__(self):
        """
        Return the number of elements in the sketch. See also the property 'nvisited'.
        """
        return len(self._heap)
    
    def __contains__(self, elt):
        """
        Return whether a given element is in the sketch

        - elt: an object as returned by the method `make_elt()` 
        """
        return elt in self._heapset

    def add_hashvalues(self, values):
        make_elt = self._make_elt
        heaptop = heap[0][0]
        for h in values:
            if h  >= heaptop:
                elt = make_elt(h, None)
                if elt not in heapset:
                    out = self._replace((h, ngram))
                    heaptop = heap[0][0]
        
    def add(self, s, w=100, hashtype="Q"):
        """ Add all ngrams/kmers of length self.nsize found in the sequence "s".

        - s: a bytes-like sequence than can be sliced, and the slices be consummed
             by the function in the property `hashfun` (given to the constructor)
        - w: width of the sequence in a batch
        - hashtype: type for hashed values

        """
        hashfun = self._hashfun
        heap = self._heap
        heapset = self._heapset
        maxsize = self._maxsize
        nsize = self._nsize
        assert nsize <= w
        anynew = self._anynew
        i = None
        lheap = len(heap)
        hashbuffer = array.array(hashtype, [0,]*w)
        if lheap > 0:
            heaptop = heap[0][0]
        else:
            heaptop = None
            
        for i in range(0, len(s)-nsize+1, w):
            subs = s[i:(i+w)]
            nsubs = hashfun(subs, nsize, hashbuffer)
            for j in range(nsubs):
                h = hashbuffer[j]
                if lheap < maxsize:
                    ngram = s[(i+j):(i+j+nsize)]
                    elt = self._make_elt(h, ngram)
                    if elt not in heapset:
                        self._add(elt)
                        heaptop = heap[0][0]
                        lheap += 1
                    if anynew is not None:
                        anynew(elt)
                elif h  >= heaptop:
                    ngram = s[(i+j):(i+j+nsize)]
                    elt = self._make_elt(h, ngram)
                    if elt not in heapset:
                        out = self._replace((h, ngram))
                        heaptop = heap[0][0]
                    if anynew is not None:
                        anynew(elt)
            self._nvisited += nsubs

    def update(self, obj):
        """
        Update the sketch with elements from `obj`.

        - obj: an iterable of elements (each element as returned by `_make_elt()`
        """
        for x in obj:
            self.add(x)
            
    def __iter__(self):
        """
        Return an iterator over the elements in the sketch.
        """
        return iter(sorted(self._heap))

def test_MaxHashNgramSketch():

    import random
    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(50))

    from mashingpumpkins._murmurhash3 import hasharray
    hashfun = hasharray
    nsize = 21
    maxsize = 10
    mhs = MaxHashNgramSketch(nsize, maxsize, hashfun)
    assert mhs.maxsize == maxsize
    assert mhs.nsize == nsize
    mhs.add(sequence)
    assert mhs.nvisited == (50-nsize+1)
    assert len(mhs) == maxsize
    assert len(mhs._heap) == maxsize
    assert len(mhs._heapset) == maxsize
    assert len(tuple(mhs)) == maxsize
    
    allhash = list()
    hbuffer = array.array('Q', [0, ])
    for i in range(0, len(sequence)-nsize):
        ngram = sequence[i:(i+nsize)]
        hashfun(ngram, nsize, hbuffer)
        allhash.append((hbuffer[0], ngram))
    allhash.sort(reverse=True)
    maxhash = set(allhash[:maxsize])
    assert len(maxhash ^ mhs._heapset) == 0
    
    #FIXME: add test for .add_hashvalues
    #FIXME: add test for .update
    

class MaxHashNgramCountSketch(MaxHashNgramSketch):
    """
    MaxHash Sketch where the number of times an hash value occurs is stored
    """

    def __init__(self, nsize: int, maxsize: int, hashfun,
                 heap : list = None,
                 count : Counter = None,
                 nvisited: int = 0):
        super().__init__(nsize, maxsize, hashfun,
                         heap = heap, nvisited = nvisited)
        if count is None:
            count = Counter()
            if heap is not None:
                for elt in heap:
                    if elt in count:
                        raise ValueError('Elements in the heap must be unique.')
                    else:
                        count[elt] = 1
        else:
            if len(self._heapset ^ set(count.keys())) > 0:
                raise ValueError("Mismatching keys with the parameter 'count'.")
        self._count = count

    def _add(self, elt):
        super()._add(elt)

    def _replace(self, elt):
        out = super()._replace(elt)
        del(self._count[out])
        return out

    def __contains__(self, elt):
        return elt in self._heapcount

    def _anynew(self, elt):
        self._count[elt] += 1

def test_MaxHashNgramCountSketch():

    import random
    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(50))

    from mashingpumpkins._murmurhash3 import hasharray
    hashfun = hasharray

    nsize = 2
    maxsize = 10
    mhs = MaxHashNgramCountSketch(nsize, maxsize, hashfun)
    assert mhs.maxsize == maxsize
    assert mhs.nsize == nsize
    mhs.add(sequence)
    assert mhs.nvisited == (50-nsize+1)

    allcounthash = Counter()
    hbuffer = array.array('Q', [0,])
    for i in range(0, len(sequence)-nsize+1):
        ngram = sequence[i:(i+nsize)]
        hashfun(ngram, nsize, hbuffer)
        allcounthash[(hbuffer[0], ngram)] += 1
    maxhash = sorted(allcounthash.keys(), reverse=True)[:maxsize]
    assert len(set(maxhash) ^ mhs._heapset) == 0

    for elt, value in mhs._count.items():
        assert allcounthash[elt] == value

    #FIXME: look the tests below
    #assert len(mhs) == maxsize
    #assert len(mhs._heap) == maxsize
    #assert len(mhs._heapset) == maxsize
    #assert len(mhs._count) == maxsize
    #assert len(tuple(mhs)) == maxsize

    #FIXME: add test for .add_hashvalues
    #FIXME: add test for .update

    
class FrozenHashNgramSketch(object):

    def __init__(self, sketch : set, nsize : int, maxsize : int, nvisited: int = 0):
        self._sketch = frozenset(sketch)
        self._nsize = nsize
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
        """ Number of ngrams / kmers visited (considered for inclusion) so far. """
        return self._nvisited

    def jaccard(self, obj):
        return len(self._sketch.intersection(obj._sketch)) /  len(self._sketch.union(obj._sketch))

    def __len__(self):
        return len(self._sketch)

def test_FrozenHashNgramSketch():
    
    nsize = 2
    maxsize = 5
    sketch = set((1,2,3,4,5))
    nvisited = len(sketch)
    mhs = FrozenHashNgramSketch(sketch, nsize, maxsize, nvisited=nvisited)
    assert mhs.maxsize == maxsize
    assert mhs.nsize == nsize
    assert mhs.nvisited == nvisited
    assert len(mhs) == maxsize
    assert len(mhs._sketch) == maxsize
    
    assert mhs.jaccard(mhs) == 1
    sketch = set((1,2,3,6,7))
    mhs_b = FrozenHashNgramSketch(sketch, nsize, maxsize, nvisited=len(sketch))
    assert mhs.jaccard(mhs_b) == 3/7

