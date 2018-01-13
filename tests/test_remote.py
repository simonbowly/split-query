''' Fixed tests for conversion of expressions to SOQL strings. '''

from datetime import datetime
import functools

import pytest

from split_query.remote import to_soql
from split_query.core.expressions import And, Or, Not, In, Eq, Le, Lt, Ge, Gt, Attribute


col1 = Attribute('column1')

TESTCASES_TO_SOQL = [
    (1, "1"),
    (1.2, "1.2"),
    ("loc", "'loc'"),
    (datetime(2016, 5, 1, 10, 22, 1), "'2016-05-01T10:22:01'"),
    (Eq(col1, 1), "column1 = 1"),
    (Ge(col1, 1), "column1 >= 1"),
    (Gt(col1, 1), "column1 > 1"),
    (Le(col1, 1), "column1 <= 1"),
    (Lt(col1, 1), "column1 < 1"),
    (In(col1, [1, 2]), "column1 in (1,2)"),
    (And(['a', 'b', 'c']), "('a') and ('b') and ('c')"),
    (Or(['a', 'b', 'c']), "('a') or ('b') or ('c')"),
    (Not('a'), "not ('a')"),
]


@pytest.mark.parametrize('expression, expected', TESTCASES_TO_SOQL)
def test_soql(expression, expected):
    assert to_soql(expression) == expected
