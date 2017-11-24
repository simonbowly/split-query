
from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import strategies as st
from hypothesis import event, given

from split_query.domain import (get_attributes, simplify_domain,
                                simplify_intervals_univariate)
from split_query.exceptions import SimplifyError
from split_query.expressions import (And, Attribute, Eq, Ge, Gt, In, Le, Lt,
                                     Not, Or)

from .strategies import float_expressions

TESTCASES_GET_ATTRIBUTES = [
    (Gt(Attribute('col1'), 1), {Attribute('col1')}),
    (Ge(Attribute('col2'), 1), {Attribute('col2')}),
    (Lt(Attribute('col3'), 1), {Attribute('col3')}),
    (Le(Attribute('col4'), 1), {Attribute('col4')}),
    (Not(Le(Attribute('col5'), 1)), {Attribute('col5')}),
    (
        And([Ge(Attribute('col6'), 3), Le(Attribute('col7'), 4)]),
        {Attribute('col6'), Attribute('col7')}),
    (
        And([Ge(Attribute('col8'), 3), Le(Attribute('col9'), 4)]),
        {Attribute('col8'), Attribute('col9')}),
    # (
    #     And([Eq(DateTime('x'), 1), Eq(Attribute('x'), 1)]),
    #     {DateTime('x'), Attribute('x')}),
    (True, set()),
    (False, set()),
    (In(Attribute('s1'), [1, 2, 3]), {Attribute('s1')}),
]


@pytest.mark.parametrize('expression, columns', TESTCASES_GET_ATTRIBUTES)
def test_get_attributes(expression, columns):
    assert get_attributes(expression) == columns


X1 = Attribute('x1')
X2 = Attribute('x2')
DT1 = Attribute('dt1')
DT2 = Attribute('dt2')
DTBASE = datetime(2017, 1, 2, 3, 0, 0, 0, timezone.utc)
DAY = timedelta(days=1)
STR = Attribute('x')


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
    # Intervals using datetime variables and values.
    (Ge(DT1, DTBASE), Ge(DT1, DTBASE)),
    (
        And([Gt(DT1, DTBASE), Lt(DT1, DTBASE + DAY * 10)]),
        And([Gt(DT1, DTBASE), Lt(DT1, DTBASE + DAY * 10)])),
    (
        And([Le(DT1, DTBASE + DAY * 5), Lt(DT1, DTBASE + DAY * 10)]),
        Le(DT1, DTBASE + DAY * 5)),
    (
        Eq(DT1, DTBASE + DAY + timedelta(milliseconds=1)),
        Eq(DT1, DTBASE + DAY + timedelta(milliseconds=1))),
    (And([Gt(DT1, DTBASE + DAY), Lt(DT1, DTBASE)]), False),
    (Or([Gt(DT1, DTBASE + DAY), Lt(DT1, DTBASE + DAY * 2)]), True),
    (
        Lt(X1, datetime(2016, 1, 1, 0, 0, 0)),
        Lt(X1, datetime(2016, 1, 1, 0, 0, 0))),
    # Irreducible sets
    (In(STR, ['1', '2', '3']), In(STR, ['1', '2', '3'])),
    (Not(In(STR, ['1', '2'])), Not(In(STR, ['1', '2']))),
    # Reducible sets AND
    (
        And([In(STR, ['a']), In(STR, ['b'])]),
        False),
    (
        And([Not(In(STR, ['a'])), Not(In(STR, ['b']))]),
        Not(In(STR, ['a', 'b']))),
    (
        And([In(STR, ['1', '2']), In(STR, ['2', '3'])]),
        In(STR, ['2'])),
    (
        And([Not(In(STR, ['1', '2'])), Not(In(STR, ['2', '3']))]),
        Not(In(STR, ['1', '2', '3']))),
    (
        And([In(STR, ['1', '2']), Not(In(STR, ['2', '3']))]),
        In(STR, ['1'])),
    (
        And([In(STR, ['a', 'b']), Not(In(STR, ['a', 'b']))]),
        False),
    (
        And([In(X1, [28, 29]), Not(In(X1, [27])), Not(In(X1, [28]))]),
        In(X1, [29])),
    (
        And([Not(In(X1, [27])), Not(In(X1, [28]))]),
        Not(In(X1, [27, 28]))),
    (
        And([In(X1, [27]), In(X1, [28, 29]), Not(In(X1, [28]))]),
        False),
    # Reducible sets OR
    (
        Or([In(STR, ['a']), In(STR, ['b'])]),
        In(STR, ['a', 'b'])),
    (
        Or([Not(In(STR, ['a'])), Not(In(STR, ['b']))]),
        True),
    (
        Or([In(STR, ['1', '2']), In(STR, ['2', '3'])]),
        In(STR, ['1', '2', '3'])),
    (
        Or([Not(In(STR, ['1', '2'])), Not(In(STR, ['2', '3']))]),
        Not(In(STR, ['2']))),
    (
        Or([In(STR, ['1', '2']), Not(In(STR, ['2', '3']))]),
        Not(In(STR, ['3']))),
    (
        Or([In(STR, ['a', 'b']), Not(In(STR, ['a', 'b']))]),
        True),
    # Edge cases and literals
    (In(X1, []), False),
    (Not(In(X1, [])), True),

    (Or([Not(In(X1, []))]), True),
    (Or([In(X1, [])]), False),
    (Or([In(X1, ['1']), False]), In(X1, ['1'])),
    (Or([In(X1, ['1']), True]), True),

    (And([In(X1, [])]), False),
    (And([Not(In(X1, []))]), True),
    (And([In(X1, ['1']), False]), False),
    (And([In(X1, ['1']), True]), In(X1, ['1'])),
]


@pytest.mark.parametrize('expression, result', TESTCASES_SIMPLIFY_INTERVALS_UNIVARIATE)
def test_simplify_intervals_univariate(expression, result):
    assert simplify_intervals_univariate(expression) == result


@pytest.mark.parametrize('expression', [
    # Attempting to simplify multivariate.
    And([Lt(X1, 1), Lt(X2, 2)]),
    # No variables in expression.
    True,
    Or([True, False]),
    # Mixed type filters on same variable.
    And([Gt(DT1, 2), Lt(DT1, DTBASE + DAY * 5)]),
    # Timezone-naive and aware datetimes.
    And([
        Lt(X1, DTBASE + DAY * 5),
        Lt(X1, datetime(2016, 1, 1, 0, 0, 0))]),
    # Mixed discrete and continuous filters.
    And([In(X1, [1, 2, 3]), Gt(X1, 2)]),
    ])
def test_simplify_intervals_univariate_error(expression):
    ''' Errors should be raised when using interval simplification
    on more than one dimension. '''
    with pytest.raises(SimplifyError):
        simplify_intervals_univariate(expression)


@given(float_expressions('xy'))
def test_simplify_intervals_univariate_fuzz(expression):
    ''' Fuzz test, checking complicated expressions defined by this strategy
    do not cause errors in domain conversion. Checks that an error is raised
    in multivariate cases. '''
    n_vars = len(get_attributes(expression))
    event('variables: {}'.format(n_vars))
    if n_vars == 0:
        with pytest.raises(SimplifyError):
            simplify_intervals_univariate(expression)
    elif n_vars == 1:
        # Domain simplifier should handle any univariate case.
        simplify_intervals_univariate(expression)
    elif n_vars == 2:
        # Expect error in multivariate cases.
        with pytest.raises(SimplifyError):
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
