''' Tests the pandas engine, but the fixed test cases given here should be
satisfied by eveny engine implementation. '''

import itertools
from datetime import datetime, timedelta

import pandas as pd
import pytest
import pytz

from split_query.engine import query_df
from split_query.core.expressions import (
    And, Attribute, Eq, Ge, Gt, In, Le, Lt, Not, Or)


x, y = [Attribute(n) for n in 'xy']
dtx = Attribute('dtx')
point = Attribute('point')

DTBASE = datetime(2017, 1, 2, 3, 0, 0, 0, pytz.utc)
DAY = timedelta(days=1)

_data = itertools.product(range(5), repeat=2)
_func = lambda entry: pd.Series(dict(entry, point='{x}:{y}'.format(**entry), dtx=DTBASE + DAY * entry['x']))
SOURCE_2D = pd.DataFrame(columns=['x', 'y'], data=list(_data)).apply(_func, axis='columns')


TESTCASES_QUERY = [
    (False, []),
    (
        And([Gt(y, 2), Not(Eq(x, 2))]),
        ['0:3', '1:3', '3:3', '4:3',
         '0:4', '1:4', '3:4', '4:4']),
    (
        And([Ge(x, 3), Lt(y, 2)]),
        ['3:0', '4:0', '3:1', '4:1']),
    (
        Or([Le(x, 1), Eq(x, 3)]),
        ['0:0', '0:1', '0:2', '0:3', '0:4',
         '1:0', '1:1', '1:2', '1:3', '1:4',
         '3:0', '3:1', '3:2', '3:3', '3:4']),
    (
        In(point, ['0:0', '1:1', '2:4']),
        ['0:0', '1:1', '2:4']),
    (
        And([
            Ge(dtx, DTBASE + DAY * 3), Le(y, 2),
            Not(In(point, ['3:1', '4:0']))]),
        ['3:0', '3:2', '4:1', '4:2']),
]


@pytest.mark.parametrize('query, expected', TESTCASES_QUERY)
def test_query_df(query, expected):
    ''' Known tests: API guarantee. '''
    result = query_df(SOURCE_2D, query)
    assert set(result['point']) == set(expected)
