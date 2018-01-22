
import json

from hypothesis import given
import msgpack

from split_query.core.serialise import default, object_hook
from .strategies import *


@given(expression_recursive(
    st.one_of(
        continuous_numeric_relation('x'),
        discrete_string_relation('tag'),
        datetime_relation('dt'),
        datetime_relation('dt-tz', timezones=st.just(pytz.utc))),
    max_leaves=100))
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
