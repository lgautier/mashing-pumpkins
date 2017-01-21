import sourmash_lib
import sourmash_lib.signature
import sourmash_lib._minhash
from mashingpumpkins.minhashsketch import MinHashNgramSketch
from mashingpumpkins import _murmurhash3_mash
from array import array

DEFAULT_SEED = 42 #sourmash_lib._minhash.MINHASH_DEFAULT_SEED


compl_tbl = bytearray(256)
for x,y in zip(b'ATGCN', b'TACGN'):
    compl_tbl[x] = y

# FIXME: masking translation table currently unused
maskatgc_tbl = bytearray(256)
for x,y in zip(b'ATGCN', b'ATGCN'):
    maskatgc_tbl[x] = y

sourmashmaskatgc_tbl = bytearray([ord(b'N'),]*256)
for x,y in zip(b'ATGC', b'ATGC'):
    sourmashmaskatgc_tbl[x] = y

def revcomp(sequence):
    ba = bytearray(sequence)
    ba.reverse()
    ba = ba.translate(compl_tbl)
    return ba

def mash_hashfun(sequence, nsize, buffer=array('Q', [0,]*300), seed=DEFAULT_SEED):
    sequence = sequence.translate(sourmashmaskatgc_tbl)
    res =  _murmurhash3_mash.hasharray_withrc(sequence, revcomp(sequence), nsize, buffer, seed)
    return res

def to_sourmashsignature(obj,
                         is_protein=False,
                         email=None,
                         name='',
                         filename=''):
    
    if not isinstance(obj, MinHashNgramSketch):
        raise ValueError("The obj must be a MinHashNgramSketch.")

    if not obj._hashfun is mash_hashfun:
        raise ValueError("The only accepted hash function is %s." % str(mash_hashfun))

    estimator = sourmash_lib.Estimators(n = obj.maxsize,
                                        ksize = obj.nsize,
                                        is_protein = is_protein,
                                        with_cardinality = False,
                                        track_abundance = False,
                                        max_hash = 0, # ???
                                        seed = obj.seed)
    for h in obj._heapset:
        estimator.mh.add_hash(h)
        
    return sourmash_lib.signature.SourmashSignature(email, estimator, name, filename)

def from_sourmashsignature(obj):
    
    assert isinstance(obj, sourmash_lib.signature.SourmashSignature)

    hashfun = mash_hashfun
    seed = DEFAULT_SEED
    maxsize = obj.estimator.num
    nsize = obj.estimator.ksize
         
    res = MinHashNgramSketch(nsize, maxsize, hashfun, seed)
    res.add_hashvalues(obj.estimator.mh.get_mins())
    return res
