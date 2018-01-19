''' Tests expansions to disjunctive normal form using truth tables. '''

import pytest
from frozendict import frozendict
from hypothesis import strategies as st
from hypothesis import event, given

from split_query.core import And, Not, Or, get_clauses, expand_dnf
from split_query.core.expand import truth_table
from .strategies import expression_trees

TABLE_1D = [dict(a=True),dict(a=False)]

TABLE_2D = [
    dict(a=True, b=True), dict(a=True, b=False),
    dict(a=False, b=True), dict(a=False, b=False)]


@pytest.mark.parametrize('expression, expected', [
    (And(['a', 'b']), zip(TABLE_2D, [True, False, False, False])),
    (Or(['a', 'b']), zip(TABLE_2D, [True, True, True, False])),
    (And(['a', Not('a')]), zip(TABLE_1D, [False, False])),
    (Or(['a', Not('a')]), zip(TABLE_1D, [True, True])),
])
def test_truth_table(expression, expected):
    ''' Test that truth_table expands out all True/False possibilities. '''
    result = {
        frozendict(assignments): result
        for assignments, result in truth_table(expression)}
    expected = {
        frozendict(assignments): result
        for assignments, result in expected}
    assert result == expected


@pytest.mark.parametrize('expression, result', [
    ('a', Or([And(['a'])])),
    (And(['a', 'b']), Or([And(['a', 'b'])])),
    (Or(['a', 'b']), Or([
        And(['a', 'b']), And([Not('a'), 'b']), And(['a', Not('b')])])),
    (And(['a', Not('a')]),                          False),
    (And([And(['a', 'b']), Not(And(['a', 'b']))]),  False),
    (Or(['a', Not('a')]),                           True),
    (Or([And(['a', 'b']), Not(And(['a', 'b']))]),   True),
])
def test_expand_dnf(expression, result):
    ''' Test complete expansion of simple relations to DNF. '''
    assert expand_dnf(expression) == result


@given(st.sampled_from(['abc', 'abcdef']).flatmap(lambda names: expression_trees(
    st.sampled_from(list(names)), max_depth=3, min_width=2, max_width=3)))
def test_expand_dnf_fuzz(expression):
    ''' Test DNF expansions on expressions with a limited number of variables.
    Asserts that the result is actually in DNF form, i.e. in the form of And
    expressions (or simpler) wrapped in a single Or expression (or simpler).
    Track statistics on the category of outputs obtained. '''
    event('Variables: {}'.format(len(get_clauses(expression))))
    result = expand_dnf(expression)
    if result is True:
        event('Result True')
    elif result is False:
        event('Result False')
    elif isinstance(result, Or):
        event('Result Or')
        assert not any(isinstance(cl, Or) for cl in result.clauses)
    elif isinstance(result, And):
        event('Result And')
        assert not any(
            isinstance(cl, Or) or isinstance(cl, And)
            for cl in result.clauses)
    elif isinstance(result, Not):
        event('Result Not')
        assert not isinstance(result.clause, And)
        assert not isinstance(result.clause, Or)
    else:
        event('Result Other')
