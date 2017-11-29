
import itertools
from datetime import datetime, timezone

import hypothesis.strategies as st
import pytest
from hypothesis import given

from split_query.core.expressions import (And, Attribute, Eq, Ge, Gt, In, Le, Lt,
                                     Not, Or, math_repr, packb, unpackb)

from .strategies import float_expressions

TESTCASES_REPR = [
    (Attribute('x'), 'x'),
    (Eq(Attribute('x'), 1), 'Eq(x,1)'),
    (Le(Attribute('z'), 2), 'Le(z,2)'),
    (Lt(Attribute('y'), 3), 'Lt(y,3)'),
    (Ge(Attribute('y'), 4), 'Ge(y,4)'),
    (Gt(Attribute('z'), 5), 'Gt(z,5)'),
    (
        Gt(Attribute('z'), datetime(2017, 1, 1, 2, 5, 0, 0, timezone.utc)),
        'Gt(z,datetime.datetime(2017, 1, 1, 2, 5, tzinfo=datetime.timezone.utc))'),
    (In(Attribute('x'), ['a', 'b']), "In(x,['a', 'b'])"),
    (And([1, 2, 3]), 'And([1, 2, 3])'),
    (Or([1, 2, 3]), 'Or([1, 2, 3])'),
    (Not(Eq(Attribute('y'), 0)), 'Not(Eq(y,0))'),
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
    # yield DateTime('x')
    yield Attribute('x')
    # yield String('x')
    for relation, attr, value in itertools.product(
            [Le, Lt, Ge, Gt, Eq], ['x', 'y'], [1, 2]):
        yield relation(attr, value)
    yield In(Attribute('x'), ['a', 'b'])
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
    (Eq(Attribute('x'), 0), 'x == 0'),
    (Le(Attribute('y'), 1), 'y <= 1'),
    (Ge(Attribute('z'), 2), 'z >= 2'),
    (Lt(Attribute('x'), 3), 'x < 3'),
    (Gt(Attribute('y'), 4), 'y > 4'),
    (Not(Eq(Attribute('x'), 1)), '~(x == 1)'),
    (
        And([Ge(Attribute('x'), 1), Le(Attribute('x'), 2), Eq(Attribute('z'), 0)]),
        '(x <= 2) & (x >= 1) & (z == 0)'),
    (
        Or([Eq(Attribute('x'), 0), Eq(Attribute('x'), 1)]),
        '(x == 0) | (x == 1)'),
    (
        Ge(Attribute('x'), datetime(2017, 1, 1, 2, 5, 0, 0, timezone.utc)),
        'x >= 2017-01-01 02:05:00+00:00'),
    (
        Lt(Attribute('x'), datetime(2017, 1, 1, 2, 5, 0, 0, timezone.utc)),
        'x < 2017-01-01 02:05:00+00:00'),
    (
        In(Attribute('x'), ['a', 'b']),
        "x in ['a', 'b']"),
]


@pytest.mark.parametrize('expression, expected', TESTCASES_MATH_REPR)
def test_math_repr(expression, expected):
    assert math_repr(expression) == expected


@pytest.mark.parametrize('expression', [tc[0] for tc in TESTCASES_REPR])
def test_msgpackable(expression):
    packed = packb(expression)
    assert isinstance(packed, bytes)
    unpacked = unpackb(packed)
    assert unpacked == expression
    assert type(unpacked) == type(expression)


@given(float_expressions('xyz'))
def test_msgpackable_fuzz(expression):
    packed = packb(expression)
    assert isinstance(packed, bytes)
    unpacked = unpackb(packed)
    assert unpacked == expression
