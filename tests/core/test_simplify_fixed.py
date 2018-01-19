''' This is a set of fixed test cases for simplify_tree and simplify_domain.

These testcases may be redundant. Simple fuzz tests check for basic guarantees
and errors, while correctness tests on mock data can validate that simplified
queries produce the same result. However, these lists are potentially useful to
document expected behaviour. They're also faster, so nice for refactoring.

    TESTCASES_SIMPLIFY_TREE         -> Input/output for simplify_tree()
    TESTCASES_SIMPLIFY_DOMAIN       -> Input/output for simplify_domain()
    TESTCASES_SIMPLIFY_DOMAIN_ERROR -> Error cases for simplify_domain()

'''

from datetime import datetime, timedelta

import pytest
import pytz

from split_query.core import (
    And, Attribute, Eq, Ge, Gt, In, Le, Lt, Not, Or, simplify_tree)


TESTCASES_SIMPLIFY_TREE = [
    # Unsimplifiable
    (And(['a', 'b']),               And(['a', 'b'])),
    (And([Or(['a', 'b']), 'c']),    And([Or(['a', 'b']), 'c'])),
    (Or([And(['a', 'b']), 'c']),    Or([And(['a', 'b']), 'c'])),
    # Flattenable
    (And([And(['a', 'b']), 'c']),   And(['a', 'b', 'c'])),
    (Or([Or(['a', 'b']), 'c']),     Or(['a', 'b', 'c'])),
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
    # traverse_expression(expression, hook=assertion_hook)  # Fails
    assert simplify_tree(expression) == expected
