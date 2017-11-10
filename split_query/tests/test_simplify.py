
from hypothesis import given, assume, event, strategies as st
import pytest

from split_query.expressions import And, Or, Not, Float
from split_query.simplify import simplify_tree
from .strategies import float_expressions, expressions


TESTCASES_SIMPLIFY_TREE = [
    # Unsimplifiable
    (And(['a', 'b']),               And(['a', 'b'])),
    # Flattenable
    (And([And(['a', 'b']), 'c']),   And(['a', 'b', 'c'])),
    (Or([Or(['a', 'b']), 'c']),     Or(['a', 'b', 'c'])),
    (And([Or(['a', 'b']), 'c']),    And([Or(['a', 'b']), 'c'])),
    (Or([And(['a', 'b']), 'c']),    Or([And(['a', 'b']), 'c'])),
    # Redundant expressions
    (And(['a']),                    'a'),
    (Or(['b']),                     'b'),
    (Not(And(['a'])),               Not('a')),
    (Not(Or(['b'])),                Not('b')),
    # Dominant literals
    (And([True, False]),            False),
    (Or([True, False]),             True),
    (And(['a', False]),             False),
    (Or([True, 'b']),               True),
    # Redundant literals
    (And(['a', 'b', True]),         And(['a', 'b'])),
    (Or(['a', 'b', False]),         Or(['a', 'b'])),
    # Fuzzed edge cases
    (And([True]),                   True),
    (Or([False]),                   False),
    # Negations
    (Not(True),                     False),
    (Not(False),                    True),
]


@pytest.mark.parametrize('expression, expected', TESTCASES_SIMPLIFY_TREE)
def test_simplify_tree(expression, expected):
    ''' Fixed tests for minimum capability of this simplifier. '''
    assert simplify_tree(expression) == expected


@given(float_expressions('xyz'))
def test_simplify_tree_fuzz(expression):
    ''' Fuzz tests to check for any infinite recursion errors. '''
    result = simplify_tree(expression)


@given(expressions(st.booleans(), max_leaves=100))
def test_simplify_tree_literal(expression):
    result = simplify_tree(expression)
    assert result is True or result is False
    if result is True:
        event("True")
    elif result is False:
        event("False")
