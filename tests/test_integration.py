''' Fuzz tests combining use of the pandas engine and expression simplification
methods to validate:
* Pandas engine handles whatever is thrown at it.
* Query after simplification gives the same result.

TODO
* Operates on 3D numeric data at the moment: needs to be extended.
* Use this to check that expand_dnf gives False when no data is returned.
This requires some more thinking: the granulatiry of the data needs to be
higher, and offset from the possible query bounds? But that may mean we can't
properly assert the difference between Ge and Gt, sooo.... thinking time.
* Don't use pandas - check data in python so this can go in the expressions test package.
* This isn't hitting the truth table expansion function!!
'''

import itertools

import pandas as pd
import pytest
from hypothesis import assume, event, given

from split_query.engine import query_df
from split_query.core import Attribute, to_dnf_simplified
from split_query.core.logic import get_variables
from .core.strategies import continuous_numeric_relation, expression_trees

x, y, z = [Attribute(n) for n in 'xyz']
dtx = Attribute('dtx')
point = Attribute('point')

_data = itertools.product(range(-10, 11, 4), repeat=3)
_func = lambda entry: pd.Series(dict(entry, point='{x}:{y}:{z}'.format(**entry)))
SOURCE_3D = pd.DataFrame(columns=['x', 'y', 'z'], data=list(_data)).apply(_func, axis='columns')


@given(expression_trees(
    continuous_numeric_relation('x') | continuous_numeric_relation('y'),
    max_depth=2, min_width=1, max_width=3))
def test_simplified_query(expression):
    ''' Fuzz everything! Checks that a simplified expression returns the
    same result as the original using the pandas engine. '''
    assume(len(get_variables(expression)) < 5)
    expression_simplified = to_dnf_simplified(expression)
    result = query_df(SOURCE_3D, expression)
    result_simplified = query_df(SOURCE_3D, expression)
    assert set(result['point']) == set(result_simplified['point'])
    event('Changed: {}'.format(expression != expression_simplified))
    if expression_simplified is True:
        event('Simplified True')
    if expression_simplified is False:
        event('Simplified False')
    npoints = len(set(result['point']))
    if npoints == 0:
        event('Empty Result')
    elif npoints == SOURCE_3D.shape[0]:
        event('Full Result')
    else:
        event('Partial Result')
