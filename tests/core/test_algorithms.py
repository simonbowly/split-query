
import pytest

from split_query.core import Attribute, And
from split_query.interface import AttributeContainer, ExpressionContainer
from split_query.core.algorithms import simplify_flat_and

x = AttributeContainer(Attribute('x'))
y = AttributeContainer(Attribute('y'))


TESTCASES = [
    # No redundancy.
    ((x < 1),                       (x < 1)),
    ((x > 1) & (x < 2),             (x > 1) & (x < 2)),
    # Redundant bounds.
    ((x < 1) & (x < 0),             (x < 0)),
    ((x > 1) & (x < 2) & (x < 3),   (x > 1) & (x < 2)),
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
    (~(x > 1),                      (x <= 1)),
    (~(x >= 2),                     (x < 2)),
    (~(x < 3),                      (x >= 3)),
    (~(x <= 4),                     (x > 4)),
    (~(x > 1) & (x > 0),            (x > 0) & (x <= 1)),
    ((x > 1) & ~(x > 0),            False),
    # Any unhandled expression is included without change.
    (
        And([(x > 0).wrapped, (x > 1).wrapped, 'exp1']),
        And([(x > 1).wrapped, 'exp1'])),
    # Set expressions.
    (x.isin([1]),                   (x == 1)),
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
]


@pytest.mark.parametrize('expression, simplified', TESTCASES)
def test_simplify_flat_and(expression, simplified):
    if isinstance(expression, ExpressionContainer):
        expression = expression.wrapped
    if isinstance(simplified, ExpressionContainer):
        simplified = simplified.wrapped
    assert simplify_flat_and(expression) == simplified
