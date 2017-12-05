''' Tests expression object representation and serialisation methods. '''

import itertools
import json

import msgpack
from hypothesis import given

from split_query.core import default, object_hook
from .strategies import (structured_3d_expressions, unique_expressions)


def test_not_equal():
    ''' Compare all combinations in the set for equality clashes. The
    implementation of expressions uses frozendicts to store data should
    guarantee this, so it is partly a stupidity check and partly a regresion
    test in case of implementation change. '''
    for a, b in itertools.combinations(unique_expressions(), 2):
        assert a != b
        assert not a == b
        assert not hash(a) == hash(b)


@given(structured_3d_expressions())
def test_expressions(expression):
    ''' Test operations on immutable expression objects. Any constructed
    expression should be hashable, repr-able and serialisable.

    Satisfied that fuzzing is enough to check for errors at the moment, but
    intend to add fixed tests (maybe just for JSON) if there is to be a stable
    serialisation format for expressions (e.g. for passing to services, etc).
    '''
    assert isinstance(hash(expression), int)
    assert isinstance(repr(expression), str)
    # Serialisation with json
    strung = json.dumps(expression, default=default)
    assert isinstance(strung, str)
    unstrung = json.loads(strung, object_hook=object_hook)
    assert unstrung == expression
    # Serialisation with msgpack
    packed = msgpack.packb(
        expression, default=default, use_bin_type=True)
    assert isinstance(packed, bytes)
    unpacked = msgpack.unpackb(
        packed, object_hook=object_hook, encoding='utf-8')
    assert unpacked == expression
