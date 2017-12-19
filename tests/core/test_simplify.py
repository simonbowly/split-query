''' Fuzz tests for methods which restructure expression trees and simplify
attribute domains. '''

import pytest
from hypothesis import strategies as st
from hypothesis import event, given

from split_query.core import And, Or, simplify_tree, traverse_expression, get_attributes, simplify_domain
from .strategies import expression_recursive, structured_3d_expressions


def assertion_hook(obj):
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
        assert not any(isinstance(cl, And) for cl in obj.clauses)
        assert len(obj.clauses) > 1
    if isinstance(obj, Or):
        assert not any(isinstance(cl, Or) for cl in obj.clauses)
        assert len(obj.clauses) > 1
    return obj


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
        traverse_expression(result, hook=assertion_hook)


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


@given(structured_3d_expressions(max_leaves=100))
def test_simplify_domain_fuzz(expression):
    ''' Expressions of three variables, which should give some opportunity
    to simplify domains. Records events to track:

    * Result was True/False/Neither
    * Result differed from simplify_tree (domain simplification was performed)
    * Result was changed/unchanged

    '''
    n_vars = len(get_attributes(expression))
    event('Variables: {}'.format(n_vars))
    result = simplify_domain(expression)
    tree_result = simplify_tree(expression)

    if result == tree_result:
        event("Same result as simplify_tree")
    else:
        event("Differs from simplify_tree")

    if result is True:
        event("Result was True")
    elif result is False:
        event("Result was False")
    else:
        event("Result neither True nor False")
        traverse_expression(result, hook=assertion_hook)

    if result == expression:
        event("Expression unaltered")
    else:
        event("Expression altered")