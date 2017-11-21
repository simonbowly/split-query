''' Maybe split this? It mixes engine and cross-package fuzzing. '''

import itertools
from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest
from hypothesis import assume, event, given

from engine import query_df
from split_query.domain import simplify_domain
from split_query.expressions import (And, Attribute, Eq, Ge, Gt, In, Le, Lt,
                                     Not, Or)
from split_query.simplify import simplify_tree
from split_query.truth_table import expand_dnf, get_clauses
from tests.strategies import float_expressions

x, y, z = [Attribute(n) for n in 'xyz']
dtx = Attribute('dtx')
point = Attribute('point')

DTBASE = datetime(2017, 1, 2, 3, 0, 0, 0, timezone.utc)
DAY = timedelta(days=1)

_data = itertools.product(range(5), repeat=2)
_func = lambda entry: pd.Series(dict(entry, point='{x}:{y}'.format(**entry), dtx=DTBASE + DAY * entry['x']))
SOURCE_2D = pd.DataFrame(columns=['x', 'y'], data=list(_data)).apply(_func, axis='columns')

_data = itertools.product(range(-10, 11, 4), repeat=3)
_func = lambda entry: pd.Series(dict(entry, point='{x}:{y}:{z}'.format(**entry)))
SOURCE_3D = pd.DataFrame(columns=['x', 'y', 'z'], data=list(_data)).apply(_func, axis='columns')


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
    result = query_df(SOURCE_2D, query)
    assert set(result['point']) == set(expected)


@given(float_expressions('xy', max_leaves=20, literals=True))
def test_query_df_fuzz(expression):
    ''' Fuzz everything! Checks that a simplified expression returns the
    same result as the original using the pandas engine. '''
    assume(len(get_clauses(expression)) < 5)
    expression = simplify_tree(expression)
    expression_simplified = simplify_domain(expand_dnf(expression))
    result = query_df(SOURCE_3D, expression)
    result_simplified = query_df(SOURCE_3D, expression)
    assert set(result['point']) == set(result_simplified['point'])
    event('Changed: {}'.format(expression != expression_simplified))
    if expression_simplified is True:
        event('Simplified True')
    if expression_simplified is False:
        event('Simplified False')
