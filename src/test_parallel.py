import pytest
import mashingpumpkins.parallel
from mashingpumpkins._murmurhash3 import hasharray
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
    cls = minhashsketch.MaxHashNgramSketch
    mashingpumpkins.parallel.Sketch.initializer(cls, nsize, maxsize, hashfun)
    hasattr(mashingpumpkins.parallel, 'sketch_constructor')
    assert type(mashingpumpkins.parallel.sketch_constructor()) is cls

def test_sketch_map_sequence():

    nsize = 21
    maxsize = 10
    hashfun = hasharray
    cls = minhashsketch.MaxHashNgramSketch
    mashingpumpkins.parallel.Sketch.initializer(cls, nsize, maxsize, hashfun)

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
    cls = minhashsketch.MaxHashNgramSketch
    mashingpumpkins.parallel.Sketch.initializer(cls, nsize, maxsize, hashfun)

    random.seed(123)
    sequence = b''.join(random.choice((b'A',b'T',b'G',b'C')) for x in range(250))
    sequences = (sequence[beg:end] for beg, end in chunkpos_iter(nsize, len(sequence), 100)) 
    mhs = mashingpumpkins.parallel.Sketch.map_sequences(sequences)

    assert mhs.nsize == nsize
    assert mhs.maxsize == maxsize
    assert mhs.nvisited == len(sequence)-nsize+1

