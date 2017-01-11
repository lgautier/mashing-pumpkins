from heapq import heappush, heapreplace
from collections import Counter

class MaxHashNgramSketch(object):
    """
    MaxHash Sketch
    """

    _anynew = None
    
    def __init__(self, nsize: int,
                 maxsize: int,
                 hashfun,
                 heap : list = None,
                 nvisited: int = 0):
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
        return self._maxsize

    @property
    def nsize(self):
        return self._nsize

    @property
    def nvisited(self):
        return self._nvisited

    def _add(self, elt):
        self._heapset.add(elt)
        heappush(self._heap, elt)

    def _replace(self, elt):
        heapset = self._heapset
        heapset.add(elt)
        out = heapreplace(self._heap, elt)
        heapset.remove(out)
        return out

    def _make_elt(self, h, ngram):
        return (h, bytes(ngram))

    def __len__(self):
        return len(self._heap)
    
    def __contains__(self, elt):
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
        
    def add(self, s):
        hashfun = self._hashfun
        heap = self._heap
        heapset = self._heapset
        maxsize = self._maxsize
        nsize = self._nsize
        anynew = self._anynew
        i = None
        lheap = len(heap)
        if lheap > 0:
            heaptop = heap[0][0]
        else:
            heaptop = None
        for i in range(0, len(s)-nsize+1):
            ngram = s[i:(i+nsize)]
            h = hashfun(ngram)
            if lheap < maxsize:
                elt = self._make_elt(h, ngram)
                if elt not in heapset:
                    self._add(elt)
                    heaptop = heap[0][0]
                    lheap += 1
                if anynew is not None:
                    anynew(elt)
            elif h  >= heaptop:
                elt = self._make_elt(h, ngram)
                if elt not in heapset:
                    out = self._replace((h, ngram))
                    heaptop = heap[0][0]
                if anynew is not None:
                    anynew(elt)
        if i is not None:
             self._nvisited += (i+1)

    def update(self, obj):
        for x in obj:
            self.add(x)
            
    def __iter__(self):
        return iter(sorted(self._heap))

def test_MaxHashNgramSketch():

    import random
    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(50))

    import mmh3
    hashfun = mmh3.hash128
    nsize = 21
    mhs = MaxHashNgramSketch(nsize, 10, hashfun)
    mhs.add(sequence)
    assert mhs.nvisited == (50-nsize+1)
    assert len(mhs) == 10
    assert len(mhs._heap) == len(mhs._heapset)
    
    allhash = list()
    for i in range(0, len(sequence)-nsize):
        ngram = sequence[i:(i+nsize)]
        allhash.append((hashfun(ngram), ngram))
    allhash.sort(reverse=True)
    maxhash = set(allhash[:10])
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

    import mmh3
    hashfun = mmh3.hash128
    nsize = 2
    nhash = 10
    mhs = MaxHashNgramCountSketch(nsize, nhash, hashfun)
    mhs.add(sequence)
    assert mhs.nvisited == (50-nsize+1)
    assert len(mhs) == nhash
    assert len(mhs._heap) == nhash
    assert len(mhs._heapset) == nhash
    assert len(mhs._count) == nhash

    allcounthash = Counter()
    for i in range(0, len(sequence)-nsize):
        ngram = sequence[i:(i+nsize)]
        allcounthash[(hashfun(ngram), ngram)] += 1
    maxhash = sorted(allcounthash.keys(), reverse=True)[:nhash]
    assert len(set(maxhash) ^ mhs._heapset) == 0

    for elt, value in mhs._count.items():
        assert allcounthash[elt] == value
    #FIXME: add test for .add_hashvalues
    #FIXME: add test for .update

    
class FrozenHashNgramSketch(object):

    def __init__(self, sketch : set, nsize : int, maxsize : int, nvisited: int = 0):
        self._sketch = frozenset(set)
        self._nsize = nsize
        self._maxsize = maxsize
        self._nvisited = nvisited

    def jaccard(self, obj):
        return len(self._sketch.intersect(obj._sketch)) /  len(self._sketch.union(obj._sketch))
