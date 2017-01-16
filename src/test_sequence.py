import pytest

from mashingpumpkins.sequence import chunkpos_iter

def test_chunkpos_iter():

    seq = tuple(range(10))
    nsize = 3
    w = 5
    for slice, check in zip(chunkpos_iter(nsize, len(seq), w),
                            ((0, 5), (3, 8), (6, 11))):
        assert slice == check
        
    w = 8
    for slice, check in zip(chunkpos_iter(nsize, len(seq), w),
                            ((0, 8), (6, 14))):
        assert slice == check

    
