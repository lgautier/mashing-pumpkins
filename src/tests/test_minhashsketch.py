import pytest

import random
import array
from collections import Counter
from mashingpumpkins import _murmurhash3, _xxhash
from mashingpumpkins.minhashsketch import (MaxSketch,
                                           MaxCountSketch,
                                           FrozenSketch,
                                           FrozenCountSketch,
                                           MinSketch,
                                           MinCountSketch)

def _allngramshashed(sequence, nsize, hashfun, seed, hashreverse):
    # list with all hash values
    allhash = list()
    hbuffer = array.array('Q', [0, ])

    # sliding window of width nsize
    for i in range(0, len(sequence)-nsize+1):
        ngram = sequence[i:(i+nsize)]
        hashfun(ngram, nsize, hbuffer, seed)
        allhash.append((hbuffer[0], ngram))

    allhash.sort(reverse=hashreverse)
    return allhash

def _test_MinMaxSketch_add(sequence, nsize, maxsize, hashfun, seed, cls):

    if cls is MaxSketch:
        hashreverse = True
    else:
        hashreverse = False
        
    mhs = cls(nsize, maxsize, hashfun, seed)
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

    allhash = _allngramshashed(sequence, nsize, hashfun, seed, hashreverse)
    
    # extract all ngrams/kmers of length nsize in the test sequence
    maxhash = set(x[0] for x in allhash[:maxsize])

    # check that the slice above matches the content of the maxhash sketch
    assert len(maxhash ^ mhs._heapset) == 0


def _test_MinMaxSketch(cls):
    nsize = 3
    maxsize = 10
    hashfun = _murmurhash3.hasharray
    seed = _murmurhash3.DEFAULT_SEED

    mhs = cls(nsize, maxsize, hashfun, seed, heap=list())
    assert len(mhs) == 0
    sequence = b'AAABBBCCC'
    mhs.add(sequence)
    hashbuffer = array.array('Q', [0,])
    hashfun(b'BBB', nsize, hashbuffer, seed)
    assert hashbuffer[0] in mhs
    assert 123 not in mhs

    # with heap
    mhs = MaxSketch(nsize, maxsize, hashfun, seed, heap=list())
    assert len(mhs) == 0

def test_MaxMaxSketch():
    _test_MinMaxSketch(MaxSketch)

def test_MinMaxSketch():
    _test_MinMaxSketch(MinSketch)
    
def _test_MinMaxSketch_longer_than_buffer(cls):
    # random (DNA) sequence
    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(250))

    # set the hashing function, size of ngrams, max size for the minhash sketch
    for hashfun, seed in ((_murmurhash3.hasharray, _murmurhash3.DEFAULT_SEED),
                          (_xxhash.hasharray, _xxhash.DEFAULT_SEED)):
        nsize = 21
        maxsize = 10
        _test_MinMaxSketch_add(sequence, nsize, maxsize, hashfun, seed, cls)

        random.seed(123)
        sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(125))
        nsize = 21
        maxsize = 10
        _test_MinMaxSketch_add(sequence, nsize, maxsize, hashfun, seed, cls)

        # test with maxsize >> len(sequence)
        nsize = 21
        maxsize = 200
        _test_MinMaxSketch_add(sequence, nsize, maxsize, hashfun, seed, cls)


def test_MaxSketch():
    _test_MinMaxSketch(MaxSketch)

def test_MinSketch():
    _test_MinMaxSketch(MinSketch)

def _test_MinMaxSketch_shorter_than_buffer(cls):
    # random (DNA) sequence
    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(50))
    nsize = 21
    maxsize = 10
    for hashfun, seed in ((_murmurhash3.hasharray, _murmurhash3.DEFAULT_SEED),
                          (_xxhash.hasharray, _xxhash.DEFAULT_SEED)):
        _test_MinMaxSketch_add(sequence, nsize, maxsize, hashfun, seed, cls)

def test_MaxSketch_shorter_than_buffer():
    _test_MinMaxSketch_shorter_than_buffer(MaxSketch)

def test_MinSketch_shorter_than_buffer():
    _test_MinMaxSketch_shorter_than_buffer(MinSketch)
    
    
def _test_MinMaxSketch_update(sequence, maxsize, methodname, cls):
    # set the hashing function, size of ngrams, max size for the minhash sketch
    hashfun = _murmurhash3.hasharray
    seed = _murmurhash3.DEFAULT_SEED
    nsize = 21
    mhs = cls(nsize, maxsize, hashfun, seed)
    mhs.add(sequence)

    mhs_a = cls(nsize, maxsize, hashfun, seed)
    seq_a = sequence[:(len(sequence)//2)]
    mhs_a.add(seq_a)
    assert mhs_a.nvisited == (len(seq_a)-nsize+1)

    # mismatching objects
    mhs_c = cls(nsize+1, maxsize, hashfun, seed)
    with pytest.raises(ValueError):
        getattr(mhs_a, methodname)(mhs_c)
    mhs_c = cls(nsize, maxsize, hashfun, seed+1)
    with pytest.raises(ValueError):
        getattr(mhs_a, methodname)(mhs_c)
    mhs_c = cls(nsize, maxsize, lambda x: 0, seed)
    with pytest.raises(ValueError):
        getattr(mhs_a, methodname)(mhs_c)
    mhs_c = cls(nsize+1, maxsize, lambda x: 0, seed)
    with pytest.raises(ValueError):
        getattr(mhs_a, methodname)(mhs_c)
    
    mhs_b = cls(nsize, maxsize, hashfun, seed)
    seq_b = sequence[(len(sequence)//2-nsize+1):]
    mhs_b.add(seq_b)
    assert mhs_b.nvisited == (len(seq_b)-nsize+1)

    res = getattr(mhs_a, methodname)(mhs_b)

    if res is None:
        # in-place method
        res = mhs_a
    assert res.nvisited == mhs.nvisited
    assert len(res) == len(mhs)
    assert len(res._heap) == len(mhs._heap)
    assert len(res._heapset) == len(mhs._heapset)
    assert len(tuple(res)) == len(tuple(mhs))

    assert len(res._heapset ^ mhs._heapset) == 0
        
def test_MinMaxSketch_update():
    methodname = 'update'
    # random (DNA) sequence
    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(250))
    maxsize = 10
    for cls in (MaxSketch, MinSketch):
        _test_MinMaxSketch_update(sequence, maxsize, methodname, cls)

    maxsize = 150
    for cls in (MaxSketch, MinSketch):
        _test_MinMaxSketch_update(sequence, maxsize, methodname, cls)

def test_MaxSketch_add():
    methodname = '__add__'
    # random (DNA) sequence
    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(250))
    maxsize = 10
    for cls in (MaxSketch, MinSketch):
        _test_MinMaxSketch_update(sequence, maxsize, methodname, cls)

    maxsize = 150
    for cls in (MaxSketch, MinSketch):
        _test_MinMaxSketch_update(sequence, maxsize, methodname, cls)


def _test_MaxSketch_add_hashvalues(nsize, maxsize, hashfun, seed):
    # random (DNA) sequence
    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(50))
    hbuffer = array.array('Q', [0, ])

    mhs_a = MaxSketch(nsize, maxsize, hashfun, seed)
    mhs_a.add(sequence)

    seq_hash = list()
    for i in range(0, len(sequence)-nsize+1):
        ngram = sequence[i:(i+nsize)]
        hashfun(ngram, nsize, hbuffer, seed)
        seq_hash.append((ngram, hbuffer[0]))

    return (sequence, seq_hash, mhs_a)


def test_MaxSketch_add_hashvalues():

    nsize = 21
    maxsize=10
    hashfun = _murmurhash3.hasharray
    seed = _murmurhash3.DEFAULT_SEED
    sequence, seq_hash, mhs_a = _test_MaxSketch_add_hashvalues(nsize, maxsize, hashfun, seed)
    mhs_b = MaxSketch(nsize, maxsize, hashfun, seed)
    hbuffer = array.array('Q', [0, ])

    mhs_b.add_hashvalues(x[1] for x in seq_hash)

    assert mhs_b.nvisited == 0 # !!! nvisited it not updated
    assert len(mhs_b) == maxsize
    assert len(mhs_b._heap) == maxsize
    assert len(mhs_b._heapset) == maxsize
    assert len(tuple(mhs_b)) == maxsize
    
    assert len(set(x[0] for x in mhs_a) ^ set(x[0] for x in mhs_b)) == 0


def test_MaxSketch_add_hashvalues_2calls():

    nsize = 21
    maxsize=10
    hashfun = _murmurhash3.hasharray
    seed = _murmurhash3.DEFAULT_SEED
    sequence, seq_hash, mhs_a = _test_MaxSketch_add_hashvalues(nsize, maxsize, hashfun, seed)
    mhs_b = MaxSketch(nsize, maxsize, hashfun, seed)
    hbuffer = array.array('Q', [0, ])

    mhs_b = MaxSketch(nsize, maxsize, hashfun, seed)
    hbuffer = array.array('Q', [0, ])
    i = 3
    mhs_b.add_hashvalues(x[1] for x in seq_hash[:i])
    assert len(mhs_b) < maxsize
    assert len(mhs_b._heap) < maxsize
    assert len(mhs_b._heapset) < maxsize
    assert len(tuple(mhs_b)) < maxsize

    mhs_b.add_hashvalues(x[1] for x in seq_hash[i:])

    assert mhs_b.nvisited == 0 # !!! nvisited it not updated
    assert len(mhs_b) == maxsize
    assert len(mhs_b._heap) == maxsize
    assert len(mhs_b._heapset) == maxsize
    assert len(tuple(mhs_b)) == maxsize
    
    assert len(set(x[0] for x in mhs_a) ^ set(x[0] for x in mhs_b)) == 0


def _test_CountSketch(cls):

    hashfun = _murmurhash3.hasharray
    seed = _murmurhash3.DEFAULT_SEED
    
    nsize = 2
    maxsize = 10
    mhs = cls(nsize, maxsize, hashfun, seed)
    assert mhs.maxsize == maxsize
    assert mhs.nsize == nsize

    nsize = 2
    maxsize = 10
    mhs = cls(nsize, maxsize, hashfun, seed, count=Counter())
    assert mhs.maxsize == maxsize
    assert mhs.nsize == nsize

    # invalid count
    with pytest.raises(ValueError):
        mhs = cls(nsize, maxsize, hashfun, seed, count=Counter([(213, 'AA')]))

    # valid heap
    mhs = cls(nsize, maxsize, hashfun, seed, heap=[])
    assert mhs.maxsize == maxsize
    assert mhs.nsize == nsize
    
    # invalid heap
    with pytest.raises(ValueError):
        mhs = cls(nsize, maxsize, hashfun, seed, heap=[(1, 'A'),(1, 'B')])

    # invalid count/heap combo
    with pytest.raises(ValueError):
        mhs = cls(nsize, maxsize, hashfun, seed,
                  heap=[(1, 'A'),(1, 'B')],
                  count=Counter([(213, 'AA')]))

def test_MaxCountSketch():
    _test_CountSketch(MaxCountSketch)

def test_MinCountSketch():
    _test_CountSketch(MinCountSketch)

def _test_CountSketch_add(cls, reverse):
    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(50))

    hashfun = _murmurhash3.hasharray
    seed = _murmurhash3.DEFAULT_SEED

    nsize = 2
    maxsize = 10
    mhs = cls(nsize, maxsize, hashfun, seed)
    assert mhs.maxsize == maxsize
    assert mhs.nsize == nsize
    
    mhs.add(sequence)
    assert mhs.nvisited == (50-nsize+1)

    allcounthash = Counter()
    hbuffer = array.array('Q', [0,])
    for i in range(0, len(sequence)-nsize+1):
        ngram = sequence[i:(i+nsize)]
        hashfun(ngram, nsize, hbuffer, seed)
        allcounthash[hbuffer[0]] += 1
    maxhash = sorted(allcounthash.keys(), reverse=reverse)[:maxsize]
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

def test_MaxCountSketch_add():
    _test_CountSketch_add(MaxCountSketch, True)

def test_MinCountSketch_add():
    _test_CountSketch_add(MinCountSketch, False)


def _test_CountSketch_freeze(cls):
    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(50))

    hashfun = _murmurhash3.hasharray
    seed = _murmurhash3.DEFAULT_SEED

    nsize = 2
    maxsize = 10
    mhs = cls(nsize, maxsize, hashfun, seed)
    mhs.add(sequence)

    fmhs = mhs.freeze()
    assert mhs.maxsize == fmhs.maxsize
    assert mhs.nsize == fmhs.nsize
    assert mhs.nvisited == fmhs.nvisited

    assert len(mhs._heapset ^ fmhs._sketch) == 0

def test_MaxCountSketch_freeze():
    _test_CountSketch_freeze(MaxCountSketch)

def test_MinCountSketch_freeze():
    _test_CountSketch_freeze(MinCountSketch)


def _test_CountSketch_update(cls, reverse):
    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(50))

    hashfun = _murmurhash3.hasharray
    seed = _murmurhash3.DEFAULT_SEED
    nsize = 2
    maxsize = 10

    mhs = cls(nsize, maxsize, hashfun, seed)
    mhs.add(sequence)
    
    mhs_a = cls(nsize, maxsize, hashfun, seed)
    i = len(sequence)//2
    mhs_a.add(sequence[:i])
    assert mhs_a.nvisited == (i-nsize+1)

    mhs_b = cls(nsize, maxsize, hashfun, seed)
    mhs_b.add(sequence[(i-nsize+1):])
    assert mhs_b.nvisited == (len(sequence)-i)
    
    mhs_a.update(mhs_b)

    allcounthash = Counter()
    hbuffer = array.array('Q', [0,])
    for i in range(0, len(sequence)-nsize+1):
        ngram = sequence[i:(i+nsize)]
        hashfun(ngram, nsize, hbuffer, seed)
        allcounthash[hbuffer[0]] += 1
    maxhash = sorted(allcounthash.keys(), reverse=reverse)[:maxsize]

    
    assert len(set(maxhash) ^ mhs_a._heapset) == 0

    for h, value in mhs_a._count.items():
        assert allcounthash[h] == value

def test_MaxCountSketch_update():
    _test_CountSketch_update(MaxCountSketch, True)

def test_MinCountSketch_update():
    _test_CountSketch_update(MinCountSketch, False)


def test_FrozenSketch():
    
    nsize = 2
    maxsize = 5
    sketch = set((1,2,3,4,5))
    nvisited = len(sketch)
    
    mhs = FrozenSketch(sketch, nsize, maxsize = maxsize, nvisited=nvisited)
    assert mhs.maxsize == maxsize
    assert mhs.nsize == nsize
    assert mhs.nvisited == nvisited
    assert len(mhs) == maxsize
    assert len(mhs._sketch) == maxsize

    mhs = FrozenSketch(sketch, nsize)
    assert mhs.maxsize == maxsize
    assert mhs.nsize == nsize
    assert mhs.nvisited == nvisited
    assert len(mhs) == maxsize
    assert len(mhs._sketch) == maxsize

    sketch = set((1,2,3,6,7))
    
    # jaccard_similarity
    assert mhs.jaccard_similarity(mhs) == 1
    mhs_b = FrozenSketch(sketch, nsize, maxsize = maxsize, nvisited=len(sketch))
    assert mhs.jaccard_similarity(mhs_b) == 3/7
    
    # jaccard_correspondance
    assert mhs.jaccard_correspondance(mhs) == 1
    mhs_b = FrozenSketch(sketch, nsize, maxsize = maxsize, nvisited=len(sketch))
    assert mhs.jaccard_correspondance(mhs_b) == 3/7
    
    # jaccard_containment
    assert mhs.jaccard_containment(mhs) == 1
    mhs_b = FrozenSketch(sketch, nsize, maxsize = maxsize, nvisited=len(sketch))
    assert mhs.jaccard_containment(mhs_b) == 3/5

    # dice_similarity
    assert mhs.dice_similarity(mhs) == 1
    mhs_b = FrozenSketch(sketch, nsize, maxsize = maxsize, nvisited=len(sketch))
    assert mhs.dice_similarity(mhs_b) == 3/5

    # invalid maxsize
    with pytest.raises(ValueError):
        mhs = FrozenSketch(sketch, nsize, maxsize = len(sketch)-1)

    # invalid nvisited
    with pytest.raises(ValueError):
        mhs = FrozenSketch(sketch, nsize, nvisited = len(sketch)-1)

def test_FrozenCountSketch():
    
    nsize = 2
    maxsize = 5
    sketch = set((1,2,3,4,5))
    count = Counter()
    for elt in sketch:
        count[elt] = elt*2
    nvisited = len(sketch)
    
    mhs = FrozenCountSketch(sketch, count, nsize, maxsize = maxsize, nvisited=nvisited)
    assert mhs.maxsize == maxsize
    assert mhs.nsize == nsize
    assert mhs.nvisited == nvisited
    assert len(mhs) == maxsize
    assert len(mhs._sketch) == maxsize

    mhs = FrozenCountSketch(sketch, count, nsize)
    assert mhs.maxsize == maxsize
    assert mhs.nsize == nsize
    assert mhs.nvisited == nvisited
    assert len(mhs) == maxsize
    assert len(mhs._sketch) == maxsize

    sketch = set((1,2,3,6,7))
    
    # jaccard_similarity
    assert mhs.jaccard_similarity(mhs) == 1
    mhs_b = FrozenCountSketch(sketch, count, nsize, maxsize = maxsize, nvisited=len(sketch))
    assert mhs.jaccard_similarity(mhs_b) == 3/7
    
    # jaccard_correspondance
    assert mhs.jaccard_correspondance(mhs) == 1
    mhs_b = FrozenCountSketch(sketch, count, nsize, maxsize = maxsize, nvisited=len(sketch))
    assert mhs.jaccard_correspondance(mhs_b) == 3/7

    # jaccard_containment
    assert mhs.jaccard_containment(mhs) == 1
    mhs_b = FrozenCountSketch(sketch, count, nsize, maxsize = maxsize, nvisited=len(sketch))
    assert mhs.jaccard_containment(mhs_b) == 3/5

    # dice_similarity
    assert mhs.dice_similarity(mhs) == 1
    mhs_b = FrozenCountSketch(sketch, count, nsize, maxsize = maxsize, nvisited=len(sketch))
    assert mhs.dice_similarity(mhs_b) == 3/5

    # invalid maxsize
    with pytest.raises(ValueError):
        mhs = FrozenCountSketch(sketch, count, nsize, maxsize = len(sketch)-1)

    # invalid nvisited
    with pytest.raises(ValueError):
        mhs = FrozenCountSketch(sketch, count, nsize, nvisited = len(sketch)-1)


