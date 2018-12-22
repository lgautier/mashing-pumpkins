from mashingpumpkins.sequence import chunkpos_iter


def test_chunkpos_iter():

    seq = tuple(range(10))
    nsize = 3
    w = 5

    # |0 1 2 3 4 5 6 7 8 9|
    #  |---------|     :  :
    #  :     |---------|  :
    #  :     :   : |------|
    #  0     :   5 :   :  :
    #        3     :   8  :
    #              6      |
    for slice, check in zip(chunkpos_iter(nsize, len(seq), w),
                            ((0, 5), (3, 8), (6, len(seq)))):
        assert slice == check

    w = 8
    for slice, check in zip(chunkpos_iter(nsize, len(seq), w),
                            ((0, 8), (6, len(seq)))):
        assert slice == check

    # windows size larger than sequence
    w = int(len(seq) * 1.1)
    for slice, check in zip(chunkpos_iter(nsize, len(seq), w),
                            ((0, len(seq)), )):
        assert slice == check
