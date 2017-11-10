
from hypothesis import given, event, strategies as st
import pytest

from split_query.expressions import Float, Eq, Le, Lt, Ge, Gt, And, Or, Not
from split_query.domain import get_attributes, simplify_intervals_univariate, simplify_domain
from .strategies import float_expressions


TESTCASES_GET_ATTRIBUTES = [
    (Gt(Float('col1'), 1), {Float('col1')}),
    (Ge(Float('col2'), 1), {Float('col2')}),
    (Lt(Float('col3'), 1), {Float('col3')}),
    (Le(Float('col4'), 1), {Float('col4')}),
    (Not(Le(Float('col5'), 1)), {Float('col5')}),
    (
        And([Ge(Float('col6'), 3), Le(Float('col7'), 4)]),
        {Float('col6'), Float('col7')}),
    (
        And([Ge(Float('col8'), 3), Le(Float('col9'), 4)]),
        {Float('col8'), Float('col9')}),
    (True, set()),
    (False, set()),
]


@pytest.mark.parametrize('expression, columns', TESTCASES_GET_ATTRIBUTES)
def test_get_attributes(expression, columns):
    assert get_attributes(expression) == columns


X1 = Float('x1')
X2 = Float('x2')

TESTCASES_SIMPLIFY_INTERVALS_UNIVARIATE = [
    # Simple interval and set expressions are not altered.
    (Ge(X1, 1), Ge(X1, 1)),
    (Gt(X1, 2), Gt(X1, 2)),
    (Le(X1, 3), Le(X1, 3)),
    (Lt(X1, 4), Lt(X1, 4)),
    (Eq(X1, 5), Eq(X1, 5)),
    # Inverses map correctly.
    (Not(Ge(X1, 5)), Lt(X1, 5)),
    (Not(Gt(X1, 6)), Le(X1, 6)),
    (Not(Le(X1, 7)), Gt(X1, 7)),
    (Not(Lt(X1, 8)), Ge(X1, 8)),
    # Compound of single expressions.
    (And([Ge(X1, 0)]), Ge(X1, 0)),
    (Or([Lt(X1, 1)]), Lt(X1, 1)),
    # Compound expressions that cannot be simplified.
    (And([Ge(X1, 2), Le(X1, 5)]), And([Ge(X1, 2), Le(X1, 5)])),
    (And([Gt(X1, 2), Lt(X1, 5)]), And([Gt(X1, 2), Lt(X1, 5)])),
    (Or([Lt(X1, 3), Ge(X1, 4)]), Or([Lt(X1, 3), Ge(X1, 4)])),
    (Or([Le(X1, 1), Gt(X1, 6)]), Or([Le(X1, 1), Gt(X1, 6)])),
    # Compound reducible interval expressions.
    (
        And([Ge(X1, 2), Le(X1, 7), Le(X1, 5)]),
        And([Ge(X1, 2), Le(X1, 5)])),
    (
        And([Gt(X1, 2), Lt(X1, 7), Lt(X1, 5)]),
        And([Gt(X1, 2), Lt(X1, 5)])),
    (
        And([
            And([Ge(X1, 2), Le(X1, 4)]),
            Not(And([Ge(X1, 3), Le(X1, 4)]))]),
        And([Ge(X1, 2), Lt(X1, 3)])),
    (
        And([
            And([Ge(X1, 2), Le(X1, 5)]),
            Not(And([Ge(X1, 3), Le(X1, 4)]))]),
        Or([
            And([Ge(X1, 2), Lt(X1, 3)]),
            And([Gt(X1, 4), Le(X1, 5)])])),
    # Resulting in boolean literals.
    (And([Lt(X1, 1), Gt(X1, 2)]), False),
    (Or([Le(X1, 0), Ge(X1, 0)]), True),
    # Edge cases producing finite sets
    (And([Le(X1, 0), Ge(X1, 0)]), Eq(X1, 0)),
    (
        Or([And([Le(X1, 0), Ge(X1, 0)]), And([Le(X1, 1), Ge(X1, 1)])]),
        Or([Eq(X1, 0), Eq(X1, 1)])),
    # Inputs with boolean literals.
    (And([Lt(X1, 1), False]), False),
    (And([Gt(X1, 1), True]), Gt(X1, 1)),
    (Or([Lt(X1, 1), True]), True),
    (Or([Gt(X1, 1), False]), Gt(X1, 1)),
]


@pytest.mark.parametrize('expression, result', TESTCASES_SIMPLIFY_INTERVALS_UNIVARIATE)
def test_simplify_intervals_univariate(expression, result):
    assert simplify_intervals_univariate(expression) == result


@pytest.mark.parametrize('expression', [
    And([Lt(Float('x1'), 1), Lt(Float('x2'), 2)]),
    True,
    Or([True, False]),
    ])
def test_simplify_intervals_univariate_error(expression):
    ''' Errors should be raised when using interval simplification
    on more than one dimension. '''
    with pytest.raises(ValueError):
        simplify_intervals_univariate(expression)


@given(float_expressions('xy'))
def test_simplify_intervals_univariate_fuzz(expression):
    ''' Fuzz test, checking complicated expressions defined by this strategy
    do not cause errors in domain conversion. Checks that an error is raised
    in multivariate cases. '''
    n_vars = len(get_attributes(expression))
    event('variables: {}'.format(n_vars))
    if n_vars == 0:
        with pytest.raises(ValueError):
            simplify_intervals_univariate(expression)
    elif n_vars == 1:
        # Domain simplifier should handle any univariate case.
        simplify_intervals_univariate(expression)
    elif n_vars == 2:
        # Expect error in multivariate cases.
        with pytest.raises(ValueError):
            simplify_intervals_univariate(expression)
    else:
        raise ValueError('Strategy produced unexpected result.')


TESTCASES_SIMPLIFY_DOMAIN = [
    # Boring bits
    (True, True),
    (False, False),
    # Univariate cases.
    (
        And([Ge(X1, 1), Le(X1, 2), Le(X1, 3)]),
        And([Ge(X1, 1), Le(X1, 2)])),
    (
        Or([Le(X1, 1), Ge(X1, 2), Ge(X1, 3)]),
        Or([Le(X1, 1), Ge(X1, 2)])),
    # Simple multivariate.
    (
        And([Ge(X1, 1), Ge(X1, 2), Le(X2, 1), Le(X2, 2)]),
        And([Ge(X1, 2), Le(X2, 1)])),
    (
        And([Ge(X1, 1), Ge(X1, 2), Le(X1, 3), Le(X2, 1), Le(X2, 2)]),
        And([Ge(X1, 2), Le(X1, 3), Le(X2, 1)])),
    (
        Or([Ge(X1, 1), Ge(X1, 2), Le(X2, 1), Le(X2, 2)]),
        Or([Ge(X1, 1), Le(X2, 2)])),
    (
        Or([Ge(X1, 1), Ge(X1, 2), Le(X2, 1), Le(X2, 2), Ge(X2, 5)]),
        Or([Ge(X1, 1), Le(X2, 2), Ge(X2, 5)])),
    # Nested multivariate
    (
        And([Ge(X1, 1), Ge(X1, 2), Or([Le(X2, 1), Le(X2, 2)])]),
        And([Ge(X1, 2), Le(X2, 2)])),
    (
        Or([Ge(X1, 1), Ge(X1, 2), And([Le(X2, 1), Le(X2, 2)])]),
        Or([Ge(X1, 1), Le(X2, 1)])),
    (
        Not(Or([Ge(X1, 1), Ge(X1, 2), And([Le(X2, 1), Le(X2, 2)])])),
        Not(Or([Ge(X1, 1), Le(X2, 1)]))),
]


@pytest.mark.parametrize('expression, result', TESTCASES_SIMPLIFY_DOMAIN)
def test_simplify_domain(expression, result):
    assert simplify_domain(expression) == result


@given(float_expressions('xyz'))
def test_simplify_domain_fuzz(expression):
    n_vars = len(get_attributes(expression))
    event('variables: {}'.format(n_vars))
    simplify_domain(expression)
