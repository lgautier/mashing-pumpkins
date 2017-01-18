import pytest

import array
from mashingpumpkins import _murmurhash3


def test_hasharray():
    nsize=3
    buffer = array.array('Q', [0, ])
    seed = 42
    _murmurhash3.hasharray(b"ACG", nsize, buffer, seed)
    assert buffer[0] == 1731421407650554201

    seed = 43
    _murmurhash3.hasharray(b"ACG", nsize, buffer, seed)
    assert buffer[0] != 1731421407650554201

