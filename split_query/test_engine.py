''' Maybe split this? It mixes engine and cross-package fuzzing. '''

import itertools

from hypothesis import assume, event, given
import pandas as pd
import pytest

from split_query.domain import simplify_domain
from split_query.expressions import Float, Eq, Le, Lt, Ge, Gt, And, Or, Not
from split_query.simplify import simplify_tree
from split_query.truth_table import get_clauses, expand_dnf
from engine import query_df
from tests.strategies import float_expressions


x, y, z = [Float(n) for n in 'xyz']

_data = itertools.product(range(5), repeat=2)
_func = lambda entry: pd.Series(dict(entry, point='{x}:{y}'.format(**entry)))
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
]


@pytest.mark.parametrize('query, expected', TESTCASES_QUERY)
def test_query_df(query, expected):
    result = query_df(SOURCE_2D, query)
    assert set(result['point']) == set(expected)


@given(float_expressions('xy', max_leaves=30, literals=True))
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
