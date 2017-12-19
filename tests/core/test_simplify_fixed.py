''' This is a set of fixed test cases for simplify_tree and simplify_domain.

These testcases may be redundant. Simple fuzz tests check for basic guarantees
and errors, while correctness tests on mock data can validate that simplified
queries produce the same result. However, these lists are potentially useful to
document expected behaviour. They're also faster, so nice for refactoring.

    TESTCASES_SIMPLIFY_TREE         -> Input/output for simplify_tree()
    TESTCASES_SIMPLIFY_DOMAIN       -> Input/output for simplify_domain()
    TESTCASES_SIMPLIFY_DOMAIN_ERROR -> Error cases for simplify_domain()

'''

from datetime import datetime, timedelta

import pytest
import pytz

from split_query.core import (
    And, Attribute, Eq, Ge, Gt, In, Le, Lt, Not, Or,
    simplify_domain, simplify_tree, SimplifyError)


TESTCASES_SIMPLIFY_TREE = [
    # Unsimplifiable
    (And(['a', 'b']),               And(['a', 'b'])),
    (And([Or(['a', 'b']), 'c']),    And([Or(['a', 'b']), 'c'])),
    (Or([And(['a', 'b']), 'c']),    Or([And(['a', 'b']), 'c'])),
    # Flattenable
    (And([And(['a', 'b']), 'c']),   And(['a', 'b', 'c'])),
    (Or([Or(['a', 'b']), 'c']),     Or(['a', 'b', 'c'])),
    # Redundant expressions
    (And(['a']),                    'a'),
    (Or(['b']),                     'b'),
    (Not(And(['a'])),               Not('a')),
    (Not(Or(['b'])),                Not('b')),
    # Dominant literals
    (And([True, False]),            False),
    (Or([True, False]),             True),
    (And(['a', False]),             False),
    (Or([True, 'b']),               True),
    # Redundant literals
    (And(['a', 'b', True]),         And(['a', 'b'])),
    (Or(['a', 'b', False]),         Or(['a', 'b'])),
    # Fuzzed edge cases
    (And([True]),                   True),
    (Or([False]),                   False),
    # Negations
    (Not(True),                     False),
    (Not(False),                    True),
]


X1 = Attribute('x1')
X2 = Attribute('x2')
DT1 = Attribute('dt1')
DT2 = Attribute('dt2')
DTBASE = datetime(2017, 1, 2, 3, 0, 0, 0, pytz.utc)
DAY = timedelta(days=1)
STR = Attribute('x')


TESTCASES_SIMPLIFY_DOMAIN_ERROR = [
    # Mixed type filters on same variable.
    And([Gt(DT1, 2), Lt(DT1, DTBASE + DAY * 5)]),
    # Timezone-naive and aware datetimes.
    And([
        Lt(X1, DTBASE + DAY * 5),
        Lt(X1, datetime(2016, 1, 1, 0, 0, 0))]),
    # Mixed discrete and continuous filters.
    And([In(X1, [1, 2, 3]), Gt(X1, 2)]),
]


TESTCASES_SIMPLIFY_DOMAIN = [
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
    # Testcases from simplify_tree
    # Unsimplifiable
    (And([Ge(X1, 1), Ge(X2, 1)]),                       And([Ge(X1, 1), Ge(X2, 1)])),
    (And([Or([Ge(X1, 1), Ge(X2, 1)]), Eq(DT1, 1)]),     And([Or([Ge(X1, 1), Ge(X2, 1)]), Eq(DT1, 1)])),
    (Or([And([Ge(X1, 1), Ge(X2, 1)]), Eq(DT1, 1)]),     Or([And([Ge(X1, 1), Ge(X2, 1)]), Eq(DT1, 1)])),
    # Flattenable
    (And([And([Ge(X1, 1), Ge(X2, 1)]), Eq(DT1, 1)]),    And([Ge(X1, 1), Ge(X2, 1), Eq(DT1, 1)])),
    (Or([Or([Ge(X1, 1), Ge(X2, 1)]), Eq(DT1, 1)]),      Or([Ge(X1, 1), Ge(X2, 1), Eq(DT1, 1)])),
    # Redundant expressions
    (And([Ge(X1, 1)]),                      Ge(X1, 1)),
    (Or([Ge(X2, 1)]),                       Ge(X2, 1)),
    (Not(And([Ge(X1, 1)])),                 Lt(X1, 1)),
    (Not(Or([Ge(X2, 1)])),                  Lt(X2, 1)),
    # Dominant literals
    (And([True, False]),                    False),
    (Or([True, False]),                     True),
    (And([Ge(X1, 1), False]),               False),
    (Or([True, Ge(X2, 1)]),                 True),
    # Redundant literals
    (And([Ge(X1, 1), Ge(X2, 1), True]),     And([Ge(X1, 1), Ge(X2, 1)])),
    (Or([Ge(X1, 1), Ge(X2, 1), False]),     Or([Ge(X1, 1), Ge(X2, 1)])),
    # Fuzzed edge cases
    (And([True]),                           True),
    (Or([False]),                           False),
    # Negations
    (Not(True),                             False),
    (Not(False),                            True),
]


@pytest.mark.parametrize('expression, expected', TESTCASES_SIMPLIFY_TREE)
def test_simplify_tree(expression, expected):
    ''' Fixed tests for minimum capability of this simplifier. '''
    # traverse_expression(expression, hook=assertion_hook)  # Fails
    assert simplify_tree(expression) == expected


@pytest.mark.parametrize('expression, result', TESTCASES_SIMPLIFY_DOMAIN)
def test_simplify_domain(expression, result):
    ''' Exact tests of cases that should be simplified successfully. '''
    assert simplify_domain(expression) == result


@pytest.mark.parametrize('expression', TESTCASES_SIMPLIFY_DOMAIN_ERROR)
def test_simplify_domain_error(expression):
    ''' Known error cases. '''
    with pytest.raises(SimplifyError):
        simplify_domain(expression)
