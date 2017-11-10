
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
