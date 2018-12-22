"""
Utilities to handle sequences
"""


def chunkpos_iter(nsize: int, lseq: int, w: int) -> (int, int):
    """
    Iterator of chunk indices.

    This is made to split a long sequence for the purpose of parallel
    computing on its constituting ngrams/kmers while not using any
    around the split points.

    For example, a sequence of length 10 for which we want
    ngrams/kmers of length 3 can be decomposed into the following
    chunks of length 5 would be split into the following 3 chunks:

    |0 1 2 3 4 5 6 7 8 9|
     |---------|     :  :
     :     |---------|  :
     :     :   : |------|
     0     :   5 :   :  :
           3     :   8  :
                 6      |

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
