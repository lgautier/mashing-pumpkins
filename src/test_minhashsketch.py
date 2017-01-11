import random
import array
from collections import Counter
from mashingpumpkins._murmurhash3 import hasharray
from mashingpumpkins.minhashsketch import (MaxHashNgramSketch, MaxHashNgramCountSketch, FrozenHashNgramSketch)
    
def test_MaxHashNgramSketch():

    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(50))

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

    
def test_MaxHashNgramCountSketch():

    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(50))

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

