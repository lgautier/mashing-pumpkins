import pytest
import mashingpumpkins.parallel
from mashingpumpkins._murmurhash3 import hasharray, DEFAULT_SEED
from mashingpumpkins.sequence import chunkpos_iter
from mashingpumpkins import minhashsketch
import random

def test_sketch_initializer():

    # empty initializer
    with pytest.raises(TypeError):
        mashingpumpkins.parallel.Sketch.initializer()

    nsize = 21
    maxsize = 10
    hashfun = lambda input,width,hashbuffer: None
    seed = 0
    cls = minhashsketch.MaxSketch
    mashingpumpkins.parallel.Sketch.initializer(cls, nsize, maxsize, hashfun, seed)
    hasattr(mashingpumpkins.parallel, 'sketch_constructor')
    assert type(mashingpumpkins.parallel.sketch_constructor()) is cls

def test_sketch_map_sequence():

    nsize = 21
    maxsize = 10
    hashfun = hasharray
    seed = DEFAULT_SEED
    cls = minhashsketch.MaxSketch
    mashingpumpkins.parallel.Sketch.initializer(cls, nsize, maxsize, hashfun, seed)

    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(250))
    mhs = mashingpumpkins.parallel.Sketch.map_sequence(sequence)

    assert mhs.nsize == nsize
    assert mhs.maxsize == maxsize
    assert mhs.nvisited == len(sequence)-nsize+1

def test_sketch_map_sequences():

    nsize = 21
    maxsize = 10
    hashfun = hasharray
    seed = DEFAULT_SEED
    cls = minhashsketch.MaxSketch
    mashingpumpkins.parallel.Sketch.initializer(cls, nsize, maxsize, hashfun, seed)

    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(250))
    sequences = (sequence[beg:end] for beg, end in chunkpos_iter(nsize, len(sequence), 100)) 
    mhs = mashingpumpkins.parallel.Sketch.map_sequences(sequences)

    assert mhs.nsize == nsize
    assert mhs.maxsize == maxsize
    assert mhs.nvisited == len(sequence)-nsize+1

def test_sketch_reduce_sketches():

    nsize = 21
    maxsize = 10
    hashfun = hasharray
    seed = DEFAULT_SEED
    cls = minhashsketch.MaxSketch

    mhs = cls(nsize, maxsize, hashfun, seed)
    mhs_a = cls(nsize, maxsize, hashfun, seed)
    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(250))
    mhs.add(sequence)
    mhs_a.add(sequence)

    mhs_b = cls(nsize, maxsize, hashfun, seed)
    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(250))
    mhs.add(sequence)
    mhs_b.add(sequence)

    mhs_ab = mashingpumpkins.parallel.Sketch.reduce(mhs_a, mhs_b)
    assert mhs.nsize == mhs_ab.nsize
    assert mhs.maxsize == mhs_ab.maxsize
    assert mhs.nvisited == mhs_ab.nvisited
    assert len(mhs._heapset ^ mhs_ab._heapset) == 0


def test_sketchlist_initializer():

    # empty initializer
    with pytest.raises(TypeError):
        mashingpumpkins.parallel.SketchList.initializer()

    nsize = 21
    maxsize = 10
    hashfun = lambda input,width,hashbuffer: None
    seed = 0
    clslist = (minhashsketch.MaxSketch, minhashsketch.MinSketch)

    # mistmatching lengths
    with pytest.raises(ValueError):
        mashingpumpkins.parallel.SketchList.initializer(clslist, [])

    # automagic length adjustment for argslist
    mashingpumpkins.parallel.SketchList.initializer(clslist, [(nsize, maxsize, hashfun, seed)])
    hasattr(mashingpumpkins.parallel, 'sketchlist_constructor')
    l = tuple(mashingpumpkins.parallel.sketchlist_constructor())
    assert len(l) == len(clslist)
    for elt, cls in zip(l, clslist):
        assert type(elt) is cls

    # automagic length adjustment for clslist
    argslist = [(nsize, maxsize, hashfun, seed),
                (nsize+1, maxsize, hashfun, seed)]
    mashingpumpkins.parallel.SketchList.initializer(clslist[:1],
                                                    argslist)
    hasattr(mashingpumpkins.parallel, 'sketchlist_constructor')
    l = tuple(mashingpumpkins.parallel.sketchlist_constructor())
    assert len(l) == 2
    for elt, (nsize, maxsize, hashfun, seed) in zip(l, argslist):
        assert elt.nsize == nsize
        assert elt.maxsize == maxsize
        assert elt._hashfun is hashfun
        assert elt.seed == seed


def test_sketchlist_map_sequence():

    nsize = 21
    maxsize = 10
    hashfun = hasharray
    seed = DEFAULT_SEED
    clslist = (minhashsketch.MaxSketch, minhashsketch.MinSketch)
    mashingpumpkins.parallel.SketchList.initializer(clslist, [(nsize, maxsize, hashfun, seed)])

    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(250))
    mhslist = mashingpumpkins.parallel.SketchList.map_sequence(sequence)

    for mhs in mhslist:
        assert mhs.nsize == nsize
        assert mhs.maxsize == maxsize
        assert mhs.nvisited == len(sequence)-nsize+1

def test_sketchlist_map_sequences():

    nsize = 21
    maxsize = 10
    hashfun = hasharray
    seed = DEFAULT_SEED
    cls = minhashsketch.MaxSketch
    mashingpumpkins.parallel.Sketch.initializer(cls, nsize, maxsize, hashfun, seed)

    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(250))
    sequences = (sequence[beg:end] for beg, end in chunkpos_iter(nsize, len(sequence), 100)) 
    mhs = mashingpumpkins.parallel.Sketch.map_sequences(sequences)

    assert mhs.nsize == nsize
    assert mhs.maxsize == maxsize
    assert mhs.nvisited == len(sequence)-nsize+1

def test_sketchlist_reduce_sketches():

    nsize = 21
    maxsize = 10
    hashfun = hasharray
    seed = DEFAULT_SEED
    clslist = (minhashsketch.MaxSketch, minhashsketch.MinSketch)
    mashingpumpkins.parallel.SketchList.initializer(clslist, [(nsize, maxsize, hashfun, seed)])

    mhslist = tuple(cls(nsize, maxsize, hashfun, seed) for cls in clslist)
    mhslist_a = tuple(cls(nsize, maxsize, hashfun, seed) for cls in clslist)
    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(250))
    for mhs, mhs_a in zip(mhslist,mhslist_a):
        mhs.add(sequence)
        mhs_a.add(sequence)

    mhslist_b = tuple(cls(nsize, maxsize, hashfun, seed) for cls in clslist)
    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(250))
    for mhs, mhs_b in zip(mhslist, mhslist_b):
        mhs.add(sequence)
        mhs_b.add(sequence)

    mhslist_ab = mashingpumpkins.parallel.SketchList.reduce(mhslist_a, mhslist_b)
    for mhs, mhs_ab in zip(mhslist, mhslist_ab):
        assert mhs.nsize == mhs_ab.nsize
        assert mhs.maxsize == mhs_ab.maxsize
        assert mhs.nvisited == mhs_ab.nvisited
        assert len(mhs._heapset ^ mhs_ab._heapset) == 0
