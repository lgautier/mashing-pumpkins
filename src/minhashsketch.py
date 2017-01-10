from heapq import heappush, heapreplace
from collections import Counter

class MaxHashNgramSketch(object):
    """
    MaxHash Sketch
    """

    def __init__(self, nsize: int, maxsize: int, hashfun,
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

    def _make_elt(self, h, ngram):
        return (h, bytes(ngram))

    def __len__(self):
        return len(self._heap)
    
    def __contains__(self, elt):
        return elt in self._heapset

    def add(self, s):
        hashfun = self._hashfun
        heap = self._heap
        heapset = self._heapset
        maxsize = self._maxsize
        nsize = self._nsize
        i = None
        lheap = len(heap)
        if lheap > 0:
            heaptop = heap[0][0]
        else:
            heaptop = None
        for i in range(0, len(s)-nsize):
            ngram = s[i:(i+nsize)]
            h = hashfun(ngram)
            if lheap < maxsize:
                elt = self._make_elt(h, ngram)
                if elt not in heapset:
                    self._add(elt)
                    heaptop = heap[0][0]
                    lheap += 1
            elif h  > heaptop:
                elt = self._make_elt(h, ngram)
                if elt not in heapset:
                    out = self._replace((h, ngram))
                    heaptop = heap[0][0]
        if i is not None:
             self._nvisited += (i+1)

    def update(self, obj):
        for x in obj:
            self.add(x)
            
    def __iter__(self):
        return iter(sorted(self._heap))

def test_MaxHashNgramSketch():
    import mmh3
    hashfun = mmh3.hash128
    nsize = 21
    mhs = MaxHashNgramSketch(nsize, 10, hashfun)
    import random
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(50))
    mhs.add(sequence)
    assert mhs.nvisited == (50-nsize)
    assert len(mhs) == 10
    assert len(mhs._heap) == len(mhs._heapset)
    allhash = list()
    for i in range(0, len(sequence)-nsize):
        ngram = sequence[i:(i+nsize)]
        allhash.append((hashfun(ngram), ngram))
    allhash.sort(reverse=True)
    maxhash = set(allhash[:10])
    assert len(maxhash ^ mhs._heapset) == 0


class MaxHashNgramCountSketch(object):
    """
    MaxHash Sketch where the number of times an hash value occurs is stored
    """

    def __init__(self, nsize: int, maxsize: int, hashfun,
                 heap : list = None,
                 heapcount : dict = None,
                 nvisited: int = 0):
        super(MaxHashNgramCountSketch, self).__init__(nsize, maxsize, hashfun,
                                                      heap = heap, nvisited = nvisited)
        if heapcount is None:
            heapcount = Counter()
            for elt in heap:
                if elt in heapcount:
                    raise ValueError('Elements in the heap must be unique.')
                else:
                    heapcount[elt] = 1
        self._heapcount = heapcount

    def _add(self, elt):
        heappush(self._heap, elt)
        self._heapcount[elt] += 1

    def _replace(self, elt):
        out = heappushpop(self._heap, elt)
        del(self._heapcount[out])
        self._heapcount[elt] += 1
        return out

    def __contains__(self, elt):
        return elt in self._heapcount
    
class FrozenHashNgramSketch(object):

    def __init__(self, sketch : set, nsize : int, maxsize : int, nvisited: int = 0):
        self._sketch = frozenset(set)
        self._nsize = nsize
        self._maxsize = maxsize
        self._nvisited = nvisited

    def jaccard(self, obj):
        return len(self._sketch.intersect(obj._sketch)) /  len(self._sketch.union(obj._sketch))

