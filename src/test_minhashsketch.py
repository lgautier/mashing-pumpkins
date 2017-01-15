import pytest

import random
import array
from collections import Counter
from mashingpumpkins._murmurhash3 import hasharray
from mashingpumpkins.minhashsketch import (MaxHashNgramSketch,
                                           MaxHashNgramCountSketch,
                                           FrozenHashNgramSketch)


def _test_MaxHashNgramSketch(sequence, nsize, maxsize):
    # set the hashing function, size of ngrams, max size for the minhash sketch
    hashfun = hasharray
    
    mhs = MaxHashNgramSketch(nsize, maxsize, hashfun)
    assert mhs.maxsize == maxsize
    assert mhs.nsize == nsize

    # add the sequence
    mhs.add(sequence)

    # check that all ngrams/kmers visited when adding sequence
    assert mhs.nvisited == (len(sequence)-nsize+1)

    if maxsize < mhs.nvisited:
        # check that the minhash sketch is full
        assert len(mhs) == maxsize
        assert len(mhs._heap) == maxsize
        assert len(mhs._heapset) == maxsize
        assert len(tuple(mhs)) == maxsize

    # extract all ngrams/kmers of length nsize in the test sequence
    allhash = list()
    hbuffer = array.array('Q', [0, ])
    for i in range(0, len(sequence)-nsize+1):
        ngram = sequence[i:(i+nsize)]
        hashfun(ngram, nsize, hbuffer)
        allhash.append((hbuffer[0], ngram))
    # slice the 10 biggest out
    allhash.sort(reverse=True)
    maxhash = set(mhs._extracthash(x) for x in allhash[:maxsize])

    # check that the slice above matches the content of the maxhash sketch
    assert len(maxhash ^ mhs._heapset) == 0


def test_MaxHashNgramSketch():
    nsize = 3
    maxsize = 10
    hashfun = hasharray

    mhs = MaxHashNgramSketch(nsize, maxsize, hashfun, heap=list())
    assert len(mhs) == 0
    sequence = b'AAABBBCCC'
    mhs.add(sequence)
    hashbuffer = array.array('Q', [0,])
    hashfun(b'BBB', nsize, hashbuffer)
    assert hashbuffer[0] in mhs
    assert 123 not in mhs
    
    # with heap
    mhs = MaxHashNgramSketch(nsize, maxsize, hashfun, heap=list())
    assert len(mhs) == 0
    
def test_MaxHashNgramSketch_longer_than_buffer():
    # random (DNA) sequence
    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(250))
    nsize = 21
    maxsize = 10
    _test_MaxHashNgramSketch(sequence, nsize, maxsize)

    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(125))
    nsize = 21
    maxsize = 10
    _test_MaxHashNgramSketch(sequence, nsize, maxsize)

    # test with maxsize >> len(sequence)
    nsize = 21
    maxsize = 200
    _test_MaxHashNgramSketch(sequence, nsize, maxsize)


def test_MaxHashNgramSketch_shorter_than_buffer():
    # random (DNA) sequence
    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(50))
    nsize = 21
    maxsize = 10
    _test_MaxHashNgramSketch(sequence, nsize, maxsize)

def _test_MaxHashNgramSketch_update(sequence, maxsize):
    # set the hashing function, size of ngrams, max size for the minhash sketch
    hashfun = hasharray
    nsize = 21
    mhs = MaxHashNgramSketch(nsize, maxsize, hashfun)
    mhs.add(sequence)

    mhs_a = MaxHashNgramSketch(nsize, maxsize, hashfun)
    seq_a = sequence[:(len(sequence)//2)]
    mhs_a.add(seq_a)
    assert mhs_a.nvisited == (len(seq_a)-nsize+1)
    mhs_b = MaxHashNgramSketch(nsize, maxsize, hashfun)
    seq_b = sequence[(len(sequence)//2-nsize+1):]
    mhs_b.add(seq_b)
    assert mhs_b.nvisited == (len(seq_b)-nsize+1)

    mhs_a.update(mhs_b)

    assert mhs_a.nvisited == mhs.nvisited
    assert len(mhs_a) == len(mhs)
    assert len(mhs_a._heap) == len(mhs._heap)
    assert len(mhs_a._heapset) == len(mhs._heapset)
    assert len(tuple(mhs_a)) == len(tuple(mhs_a))

    assert len(mhs_a._heapset ^ mhs._heapset) == 0

def test_MaxHashNgramSketch_update():
    # random (DNA) sequence
    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(250))
    maxsize = 10
    _test_MaxHashNgramSketch_update(sequence, maxsize)

    maxsize = 150
    _test_MaxHashNgramSketch_update(sequence, maxsize)


def test_MaxHashNgramSketch_add_hashvalues():
    # random (DNA) sequence
    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(50))

    hashfun = hasharray
    nsize = 21
    maxsize = 10
    mhs_a = MaxHashNgramSketch(nsize, maxsize, hashfun)
    mhs_a.add(sequence)

    mhs_b = MaxHashNgramSketch(nsize, maxsize, hashfun)
    hbuffer = array.array('Q', [0, ])
    seq_hash = list()
    for i in range(0, len(sequence)-nsize):
        ngram = sequence[i:(i+nsize)]
        hashfun(ngram, nsize, hbuffer)
        seq_hash.append((ngram, hbuffer[0]))    
    mhs_b.add_hashvalues(x[1] for x in seq_hash)

    assert mhs_b.nvisited == 0 # !!! nvisited it not updated
    assert len(mhs_b) == maxsize
    assert len(mhs_b._heap) == maxsize
    assert len(mhs_b._heapset) == maxsize
    assert len(tuple(mhs_b)) == maxsize
    
    assert len(set(x[0] for x in mhs_a) ^ set(x[0] for x in mhs_b)) == 0
    
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

    nsize = 2
    maxsize = 10
    mhs = MaxHashNgramCountSketch(nsize, maxsize, hashfun, count=Counter())
    assert mhs.maxsize == maxsize
    assert mhs.nsize == nsize

    # invalid count
    with pytest.raises(ValueError):
        mhs = MaxHashNgramCountSketch(nsize, maxsize, hashfun, count=Counter([(213, 'AA')]))

    
def test_MaxHashNgramCountSketch_add():

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
        allcounthash[hbuffer[0]] += 1
    maxhash = sorted(allcounthash.keys(), reverse=True)[:maxsize]
    assert len(set(maxhash) ^ mhs._heapset) == 0

    for h, value in mhs._count.items():
        assert allcounthash[h] == value

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
    
    mhs = FrozenHashNgramSketch(sketch, nsize, maxsize = maxsize, nvisited=nvisited)
    assert mhs.maxsize == maxsize
    assert mhs.nsize == nsize
    assert mhs.nvisited == nvisited
    assert len(mhs) == maxsize
    assert len(mhs._sketch) == maxsize

    mhs = FrozenHashNgramSketch(sketch, nsize)
    assert mhs.maxsize == maxsize
    assert mhs.nsize == nsize
    assert mhs.nvisited == nvisited
    assert len(mhs) == maxsize
    assert len(mhs._sketch) == maxsize

    assert mhs.jaccard(mhs) == 1
    sketch = set((1,2,3,6,7))
    mhs_b = FrozenHashNgramSketch(sketch, nsize, maxsize = maxsize, nvisited=len(sketch))
    assert mhs.jaccard(mhs_b) == 3/7
    
    # invalid maxsize
    with pytest.raises(ValueError):
        mhs = FrozenHashNgramSketch(sketch, nsize, maxsize = len(sketch)-1)

    # invalid nvisited
    with pytest.raises(ValueError):
        mhs = FrozenHashNgramSketch(sketch, nsize, nvisited = len(sketch)-1)
