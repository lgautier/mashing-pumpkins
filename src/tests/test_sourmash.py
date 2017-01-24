import pytest

from mashingpumpkins.minhashsketch import MinSketch

try:
    from mashingpumpkins.sourmash import (to_sourmashsignature,
                                          from_sourmashsignature,
                                          mash_hashfun,
                                          DEFAULT_SEED)
    has_sourmash = True
except ImportError:
    has_sourmash = False

    
@pytest.mark.skipif(not has_sourmash,
                    reason="requires sourmash_lib")
def test_to_sourmashsignature_and_back():

    nsize = 3
    maxsize = 10
    hashfun = mash_hashfun
    seed = DEFAULT_SEED
    
    # invalid hashfun
    mhns = MinSketch(nsize, maxsize, lambda x,y,z:0, seed)
    with pytest.raises(ValueError):
        sms = to_sourmashsignature(mhns)
        
    # invalid seed
    mhns = MinSketch(nsize, maxsize, lambda x,y,z:0, seed+1)
    with pytest.raises(ValueError):
        sms = to_sourmashsignature(mhns)
        
    sequence = b'AAATTTTCCCC'
    mhns = MinSketch(nsize, maxsize, mash_hashfun, seed)
    mhns.add(sequence)
    
    sms = to_sourmashsignature(mhns)
    mhns_2 = from_sourmashsignature(sms)

    assert len(mhns._heapset) == len(mhns_2._heapset)
    assert len(mhns._heapset ^ mhns_2._heapset) == 0
    
