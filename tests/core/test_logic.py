''' Fuzz tests for methods which manipulate logical structures. '''

import itertools

from hypothesis import event, given, strategies as st

from split_query.core.expressions import And, Or
from split_query.core.logic import *
from .strategies import *


@given(expression_recursive(
    st.one_of(
        continuous_numeric_relation('x'),
        discrete_string_relation('tag'),
        datetime_relation('dt'),
        datetime_relation('dt-tz', timezones=st.just(pytz.utc)),
        st.sampled_from([True, False])),
    max_leaves=100))
def test_substitution_result(expression):
    variables = get_variables(expression)
    assignments = {
        variable: assignment for variable, assignment
        in zip(variables, itertools.cycle([True, False]))}
    result = substitution_result(expression, assignments)
    event('Result: {}'.format(result))
    assert result in (True, False)


@given(st.sampled_from(['abc', 'abcdef']).flatmap(lambda names: expression_trees(
    st.sampled_from(list(names)), max_depth=3, min_width=2, max_width=3)))
def test_to_dnf_clauses(expression):
    n_variables = len(get_variables(expression))
    event('Variables: {}'.format(n_variables))
    result = list(to_dnf_clauses(expression))
    assert all(type(cl) is And for cl in result)


def validate(obj):
    ''' Throws an error if any structures which should have been simplified
    were not. This applies to any expression which is the result of
    simplify_tree or simplify_domain. The result should not contain:

    * Any boolean literals (unless the final result is True/False).
    * Any nested Ands/Ors (of the same type).
    * Any Ands/Ors with only one variable.
    '''
    assert obj is not True
    assert obj is not False
    if isinstance(obj, And):
        assert len(obj.clauses) > 1
        for cl in obj.clauses:
            assert not isinstance(cl, And)
            validate(cl)
    if isinstance(obj, Or):
        assert len(obj.clauses) > 1
        for cl in obj.clauses:
            assert not isinstance(cl, Or)
            validate(cl)


@given(expression_recursive(
    st.sampled_from(list('abcd')) | st.booleans(), max_leaves=100))
def test_simplify_tree_fuzz(expression):
    ''' Expressions containing arbitrary variables. If the result does not
    turn out to be True or False, then it must satisfy assertion_hook. '''
    result = simplify_tree(expression)
    if result is True:
        event("True")
    elif result is False:
        event("False")
    else:
        event("Other")
        validate(result)


@given(expression_recursive(st.booleans(), max_leaves=100))
def test_simplify_tree_literal(expression):
    ''' And/Or/Not trees populated entirely with True/False literals.
    Regardless of structure, simplification should always give True or False.
    '''
    result = simplify_tree(expression)
    assert result is True or result is False
    if result is True:
        event("True")
    elif result is False:
        event("False")
