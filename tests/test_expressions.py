
import datetime

from hypothesis import given, example
import pytest

from .testing import st_expressions
from octo_spork.expressions import (
    Attribute, Eq, Le, Lt, Ge, Gt, And, Or, Not, nice_repr)


@pytest.mark.parametrize('expr1, expr2', [
    (And(['a', 'b']), And(['b', 'a'])),
    (Or(['a', 'b']), Or(['b', 'a'])),
    ])
def test_expressions_equal(expr1, expr2):
    ''' Equality of expressions with the same data. '''
    assert expr1 == expr2


@pytest.mark.parametrize('expr1, expr2', [
    (And(['a', 'b']), Or(['a', 'b'])),
    (Not('a'), Attribute('a')),
    (Eq('a', 1), Le('a', 1)),
    (Lt('a', 1), Le('a', 1)),
    (Ge('a', 1), Gt('a', 1)),
    (Ge('a', 1), Le('a', 1)),
    ])
def test_expressions_unequal(expr1, expr2):
    ''' Inequality of expressions. '''
    assert not expr1 == expr2


@given(st_expressions())
@example(Attribute('c1'))
@example(Eq(Attribute('c1'), 1))
@example(Eq(Attribute('c1'), 'haha'))
@example(Eq(Attribute('c1'), datetime.datetime.now()))
@example(And([Eq(Attribute('c1'), 1), Eq(Attribute('c2'), 2)]))
@example(Or([Eq(Attribute('c1'), 1), Eq(Attribute('c2'), 2)]))
@example(Not(Eq(Attribute('c1'), 1)))
def test_hashable(expression):
    ''' Ensure constructed expression objects are hashable. '''
    hash(expression)


def test_attribute_access():
    ''' Actually testing the ExpressionBase __getattr__ parent method. '''
    attribute = Attribute('c1')
    assert attribute['name'] == 'c1'
    assert attribute.name == 'c1'
    with pytest.raises(AttributeError):
        attribute.prop


@given(st_expressions())
def test_nice_repr(expression):
    ''' Error checking string repr with complex expressions. '''
    nice_repr(expression)
