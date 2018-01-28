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
    ''' If passed a complete dictionary of True/False assignments to relations,
    substitution always gives a True/False result. '''
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
    simplify_tree. The result should not contain:

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


simple = st.sampled_from('abcd') | st.sampled_from('abcd').map(Not)
flat_and = st.lists(simple, min_size=2).map(And)
dnf = st.lists(flat_and, min_size=2).map(Or)
not_dnf = (
    dnf.map(Not) | st.lists(dnf, min_size=1).map(And) | st.lists(dnf, min_size=1).map(Or) |
    st.lists(flat_and, min_size=1).map(And))


@given(simple)
def test_simple(expression):
    assert is_simple(expression)
    assert is_flat_and(expression)
    assert is_dnf(expression)


@given(flat_and)
def test_flat_and(expression):
    assert not is_simple(expression)
    assert is_flat_and(expression)
    assert is_dnf(expression)


@given(dnf)
def test_dnf(expression):
    assert not is_simple(expression)
    assert not is_flat_and(expression)
    assert is_dnf(expression)


@given(not_dnf)
def test_not_dnf(expression):
    assert not is_dnf(expression)


varied_flat_and = st.lists(simple, min_size=1).map(lambda clauses: clauses[0] if len(clauses) == 1 else And(clauses))
varied_dnf = st.lists(varied_flat_and, min_size=1).map(lambda clauses: clauses[0] if len(clauses) == 1 else Or(clauses))
heuristic_input = varied_dnf | varied_flat_and.map(Not)
@given(st.lists(heuristic_input, min_size=2, max_size=3))
def test_heuristic(expressions):
    ''' The heuristic_input strategy always produces valid expressions which
    to_dnf_expand_heuristic should correctly expand when joined by an And
    clause. '''
    # Input stats.
    if any(is_simple(expression) for expression in expressions):
        event('Simple')
    if any(is_flat_and(expression) for expression in expressions):
        event('Flat AND')
    if any(is_dnf(expression) for expression in expressions):
        event('DNF')
    # Algebraic expansion result.
    expression = And(expressions)
    result = to_dnf_expand_heuristic(expression)
    assert is_dnf(result)
    # Truth table expansion of both (logical equivalence).
    expand_original = to_dnf_expand_truth_table(expression)
    expand_transformed = to_dnf_expand_truth_table(result)
    assert isinstance(expand_original, Or) and is_dnf(expand_original)
    assert isinstance(expand_transformed, Or) and is_dnf(expand_transformed)
    # Order is not reliable, so require set of sets comparison.
    s1 = frozenset(frozenset(cl.clauses) for cl in expand_original.clauses)
    s2 = frozenset(frozenset(cl.clauses) for cl in expand_transformed.clauses)
    assert s1 == s2
