
from datetime import datetime, timezone
import itertools

from hypothesis import given
import hypothesis.strategies as st
import pytest

from split_query.expressions import Float, DateTime, String, Eq, Le, Lt, Ge, Gt, In, And, Or, Not, math_repr
from .strategies import float_expressions


TESTCASES_REPR = [
    (DateTime('x'), 'x'),
    (Float('x'), 'x'),
    (String('x'), 'x'),
    (Eq(Float('x'), 1), 'Eq(x,1)'),
    (Le(Float('z'), 2), 'Le(z,2)'),
    (Lt(Float('y'), 3), 'Lt(y,3)'),
    (Ge(Float('y'), 4), 'Ge(y,4)'),
    (Gt(Float('z'), 5), 'Gt(z,5)'),
    (In(String('x'), ['a', 'b']), "x in ['a', 'b']"),
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
    yield DateTime('x')
    yield Float('x')
    yield String('x')
    for relation, attr, value in itertools.product(
            [Le, Lt, Ge, Gt, Eq], ['x', 'y'], [1, 2]):
        yield relation(attr, value)
    yield In(String('x'), ['a', 'b'])
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


TESTCASES_MATH_REPR = [
    (Eq(Float('x'), 0), 'x == 0'),
    (Le(Float('y'), 1), 'y <= 1'),
    (Ge(Float('z'), 2), 'z >= 2'),
    (Lt(Float('x'), 3), 'x < 3'),
    (Gt(Float('y'), 4), 'y > 4'),
    (Not(Eq(Float('x'), 1)), '~(x == 1)'),
    (
        And([Ge(Float('x'), 1), Le(Float('x'), 2), Eq(Float('z'), 0)]),
        '(x <= 2) & (x >= 1) & (z == 0)'),
    (
        Or([Eq(Float('x'), 0), Eq(Float('x'), 1)]),
        '(x == 0) | (x == 1)'),
    (
        Ge(DateTime('x'), datetime(2017, 1, 1, 2, 5, 0, 0, timezone.utc)),
        'x >= 2017-01-01 02:05:00+00:00'),
    (
        Lt(DateTime('x'), datetime(2017, 1, 1, 2, 5, 0, 0, timezone.utc)),
        'x < 2017-01-01 02:05:00+00:00'),
    (
        In(String('x'), ['a', 'b']),
        "x in ['a', 'b']"),
]


@pytest.mark.parametrize('expression, expected', TESTCASES_MATH_REPR)
def test_math_repr(expression, expected):
    assert math_repr(expression) == expected
