"""
Utilities to handle sequences
"""

def chunkpos_iter(nsize: int, lseq: int, w: int) -> (int, int):
    """
    Iterator of chunk indices.

    - nsize: n in ngram
    - lseq: length of sequence to chunk
    - w: width of window

    """

    assert nsize <= w
    ew = w-nsize+1
    
    nchunks = (lseq // ew)

    leftover = lseq - nchunks*ew

    if leftover >= nsize:
        nchunks += 1

    for w_i in range(nchunks):
        slice_beg = (w_i*ew)
        slice_end = slice_beg + w
        yield (slice_beg, min(slice_end, lseq))
