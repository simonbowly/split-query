''' Tests expression object representation and serialisation methods. '''

import itertools

from hypothesis import given

from split_query.core.expressions import Attribute, Le, Lt, Ge, Gt, Eq, In, And, Or, Not
from .strategies import *


def unique_expressions():
    ''' Pairwise combinations which should be unequal. '''
    yield Attribute('x')
    yield Attribute('y') 
    for relation, attr, value in itertools.product(
            [Le, Lt, Ge, Gt, Eq], ['x', 'y'], [1, 2]):
        yield relation(attr, value)
    for relation, attr, value in itertools.product(
            [Le, Lt, Ge, Gt, Eq], ['x', 'y'], [1, 2]):
        yield Not(relation(attr, value))
    yield In(Attribute('x'), ['a', 'b'])
    yield And(['a', 'b'])
    yield And(['a', 'c'])
    yield Or(['a', 'b'])
    yield Or(['a', 'c'])
    yield Not('a')
    yield Not('b')


def test_collisions():
    ''' Compare all combinations in the set for equality clashes and hash
    collisions. '''
    for a, b in itertools.combinations(unique_expressions(), 2):
        assert a != b
        assert not a == b
        assert not hash(a) == hash(b)
        assert not repr(a) == repr(b)


@given(expression_recursive(
    st.one_of(
        continuous_numeric_relation('x'),
        discrete_string_relation('tag'),
        datetime_relation('dt'),
        datetime_relation('dt-tz', timezones=st.just(pytz.utc))),
    max_leaves=100))
def test_expressions(expression):
    ''' Ensure any complex nested expression is still hashable. '''
    assert isinstance(hash(expression), int)
    assert isinstance(repr(expression), str)
