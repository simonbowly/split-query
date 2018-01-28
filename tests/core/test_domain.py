
import pytest

from hypothesis import event, given, strategies as st

from split_query.core import Attribute, And, Not
from split_query.core.domain import simplify_flat_and
from split_query.core.wrappers import AttributeContainer, ExpressionContainer
from .strategies import mixed_numeric_relation

x = AttributeContainer(Attribute('x'))
y = AttributeContainer(Attribute('y'))
other = ExpressionContainer('exp1')


TESTCASES = [
    # No redundancy.
    ((x > 1) & (x < 2),             (x > 1) & (x < 2)),
    # Redundant bounds.
    ((x < 1) & (x < 0),             (x < 0)),
    ((x > 1) & (x < 2) & (x < 3),   (x < 2) & (x > 1)),
    ((x > 1) & (x < 2) & (x > 0),   (x > 1) & (x < 2)),
    # Strictly lt/gt bounds are tighter.
    ((x > 1) & (x >= 1),            (x > 1)),
    ((x < 1) & (x <= 1),            (x < 1)),
    # Multivariate.
    (
        ((y > 1) & (y > 2) & (y > 3) & (x <= 1) & (x >= 1) & (x < 3)),
        ((y > 3) & (x == 1))),
    # Conflict cases.
    ((x > 2) & (x < 1),             False),
    ((x > 1) & (x < 1),             False),
    ((x >= 1) & (x < 1),            False),
    ((x > 1) & (x <= 1),            False),
    ((x >= 1) & (x <= 1),           (x == 1)),
    # Conflicting bounds on any variable give an overall False result.
    ((y > 1) & (y < 2) & (x > 2) & (x < 1), False),
    # Negations handled.
    # (~(x > 1),                      (x <= 1)),
    # (~(x >= 2),                     (x < 2)),
    # (~(x < 3),                      (x >= 3)),
    # (~(x <= 4),                     (x > 4)),
    (~(x > 1) & (x > 0),            (x > 0) & (x <= 1)),
    ((x > 1) & ~(x > 0),            False),
    # Any unhandled expression is included without change.
    ((x > 0) & (x > 1) & other,     (x > 1) & other),
    ((x > 0) & (x > 1) & ~other,    (x > 1) & ~other),
    # Set expressions.
    (
        x.isin([1, 2, 3]) & x.isin([2, 3, 4]),
        x.isin([2, 3])),
    (
        ~x.isin([1, 2, 3]) & ~x.isin([2, 3, 4]),
        ~x.isin([1, 2, 3, 4])),
    (
        x.isin([1, 2, 3]) & ~x.isin([2, 3, 4]),
        (x == 1)),
    (x.isin([1, 2, 3]) & x.isin([4, 5, 6]), False),
    (x.isin([1, 2, 3]) & ~x.isin([1, 2, 3, 4]), False),
    # Combined bounds + sets.
    ((x == 1) & (x >= 0),           (x == 1)),
    ((x == 1) & (x == 2),           False),
    (x.isin([0, 1, 2]) & (x < 2),   x.isin([0, 1])),
    (x.isin([1, 2, 3]) & (x <= 2),  x.isin([1, 2])),
    (x.isin([1, 2, 3]) & (x > 3),   False),
    # Edge cases
    (~(x == 0) & x.isin([0]),       False),
    (~(x == 0) & (x == 0),          False),
    (~(~(x == 0)) & (y == 0),       (x == 0) & (y == 0)),
    (And([True]),                   True),
    (And([False]),                  False),
    # Found in cache tests.
    (
        (x >= 2014) & (x < 2015) & ~(x == 2015),
        (x >= 2014) & (x < 2015)),
    (
        (x >= 2015) & (x <= 2015) & ~(x == 2015),
        False),
]


@pytest.mark.parametrize('expression, simplified', TESTCASES)
def test_simplify_flat_and(expression, simplified):
    ''' Obviously simplifiable cases to define algorithm behaviour. Should be
    reducible to a simpler set. '''
    if type(expression) is ExpressionContainer:
        expression = expression.wrapped
    if type(simplified) is ExpressionContainer:
        simplified = simplified.wrapped
    result = simplify_flat_and(expression)
    # Output order is not well defined, so handle equality comparison with sets.
    if type(simplified) is And:
        assert type(result) is And
        assert set(result.clauses) == set(simplified.clauses)
        assert len(set(result.clauses)) == len(result.clauses)
    else:
        assert result == simplified


@given(st.lists(st.one_of(
    mixed_numeric_relation('x'),
    mixed_numeric_relation('x').map(lambda e: Not(e)),
    mixed_numeric_relation('y'),
    mixed_numeric_relation('y').map(lambda e: Not(e)),
    ), min_size=1))
def test_simplify_flat_and_fuzz(clauses):
    ''' Currently a simple error check, but this should really validate
    algorithm guarantees by checking against a data set. '''
    result = simplify_flat_and(And(clauses))
    n_output = len(result.clauses) if type(result) is And else 1
    assert n_output <= len(clauses)
    if result is False:
        event('Simplified False')
    else:
        if n_output < len(clauses):
            event('Shortened')
