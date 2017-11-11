
import itertools

from hypothesis import given
import hypothesis.strategies as st
import pytest

from split_query.expressions import Float, Eq, Le, Lt, Ge, Gt, And, Or, Not
from .strategies import float_expressions


TESTCASES_REPR = [
    (Float('x'), 'x'),
    (Eq(Float('x'), 1), 'Eq(x,1)'),
    (Le(Float('z'), 2), 'Le(z,2)'),
    (Lt(Float('y'), 3), 'Lt(y,3)'),
    (Ge(Float('y'), 4), 'Ge(y,4)'),
    (Gt(Float('z'), 5), 'Gt(z,5)'),
    (And([1, 2, 3]), 'And([1, 2, 3])'),
    (Or([1, 2, 3]), 'Or([1, 2, 3])'),
    (Not(Eq(Float('y'), 0)), 'Not(Eq(y,0))'),
]


@pytest.mark.parametrize('expression, expected', TESTCASES_REPR)
def test_repr(expression, expected):
    ''' Fixed tests ensuring correct repr. '''
    assert repr(expression) == expected


@given(float_expressions('xyz'))
def test_hash_repr_able(expression):
    ''' Fuzz test, checking complicated expressions defined by this strategy
    do not cause errors with hash or repr. '''
    assert isinstance(hash(expression), int)
    assert isinstance(repr(expression), str)


def expressions_not_equal():
    ''' Generates distinct expressions for != testing. '''
    yield Float('x')
    for relation, attr, value in itertools.product(
            [Le, Lt, Ge, Gt, Eq], ['x', 'y'], [1, 2]):
        yield relation(attr, value)
    yield And(['a', 'b'])
    yield And(['a', 'c'])
    yield Or(['a', 'b'])
    yield Or(['a', 'c'])
    yield Not('a')
    yield Not('b')


def test_not_equal():
    ''' Compare all combinations in the set for equality clashes. The
    implementation of expressions uses frozendicts to store data should
    guarantee this, so it is partly a stupidity check and partly a regresion
    test in case of implementation change. '''
    for a, b in itertools.combinations(expressions_not_equal(), 2):
        assert a != b
        assert not a == b
        assert not hash(a) == hash(b)
