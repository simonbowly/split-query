
import pytest

from octo_spork.expressions import Attribute, Le, Lt, Ge, Gt, In, And, Or, Not
from octo_spork.domain import simplify_sets, simplify_intervals, get_attributes


col = Attribute('x1')


@pytest.mark.parametrize('expression, result', [
    # Simple interval and set expressions are not altered.
    (Ge(col, 1), Ge(col, 1)),
    (Gt(col, 2), Gt(col, 2)),
    (Le(col, 3), Le(col, 3)),
    (Lt(col, 4), Lt(col, 4)),
    # # Inverses map correctly.
    (Not(Ge(col, 5)), Lt(col, 5)),
    (Not(Gt(col, 6)), Le(col, 6)),
    (Not(Le(col, 7)), Gt(col, 7)),
    (Not(Lt(col, 8)), Ge(col, 8)),
    # # Compound of single expressions.
    (And([Ge(col, 0)]), Ge(col, 0)),
    (Or([Lt(col, 1)]), Lt(col, 1)),
    # # Compound expressions that cannot be simplified.
    (And([Ge(col, 2), Le(col, 5)]), And([Ge(col, 2), Le(col, 5)])),
    (And([Gt(col, 2), Lt(col, 5)]), And([Gt(col, 2), Lt(col, 5)])),
    (Or([Lt(col, 3), Ge(col, 4)]), Or([Lt(col, 3), Ge(col, 4)])),
    (Or([Le(col, 1), Gt(col, 6)]), Or([Le(col, 1), Gt(col, 6)])),
    # # Compound reducible interval expressions.
    (
        And([Ge(col, 2), Le(col, 7), Le(col, 5)]),
        And([Ge(col, 2), Le(col, 5)])),
    (
        And([Gt(col, 2), Lt(col, 7), Lt(col, 5)]),
        And([Gt(col, 2), Lt(col, 5)])),
    (
        And([
            And([Ge(col, 2), Le(col, 4)]),
            Not(And([Ge(col, 3), Le(col, 4)]))]),
        And([Ge(col, 2), Lt(col, 3)])),
    (
        And([
            And([Ge(col, 2), Le(col, 5)]),
            Not(And([Ge(col, 3), Le(col, 4)]))]),
        Or([
            And([Ge(col, 2), Lt(col, 3)]),
            And([Gt(col, 4), Le(col, 5)])])),
    # Resulting in boolean literals.
    (And([Lt(col, 1), Gt(col, 2)]), False),
    (Or([Le(col, 0), Ge(col, 0)]), True),
])
def test_simplify_intervals(expression, result):
    assert simplify_intervals(expression) == result


@pytest.mark.parametrize('expression', [
    (In(col, [1, 2, 3])),
    And([Lt(Attribute('x1'), 1), Lt(Attribute('x2'), 2)]),
    ])
def test_simplify_intervals_error(expression):
    with pytest.raises(ValueError):
        simplify_intervals(expression)


@pytest.mark.parametrize('expression, result', [
    # Irreducible
    (In(col, [1, 2, 3]), In(col, [1, 2, 3])),
    (Not(In(col, [1, 2])), Not(In(col, [1, 2]))),
    # Reducible
    (Or([In(col, [1, 2]), In(col, [2, 3])]), In(col, [1, 2, 3])),
    (And([In(col, [1, 2]), In(col, [2, 3])]), In(col, [2])),
    (And([In(col, [1, 2]), Not(In(col, [2, 3]))]), In(col, [1])),
])
def test_simplify_sets(expression, result):
    assert simplify_sets(expression) == result


@pytest.mark.parametrize('expression', [
    And([In(Attribute('x1'), [1, 2]), In(Attribute('x2'), [1, 2])]),
    Le(col, 1),
    Lt(col, 1),
    Ge(col, 1),
    Gt(col, 1),
    ])
def test_simplify_sets_error(expression):
    with pytest.raises(ValueError):
        simplify_sets(expression)


@pytest.mark.parametrize('expression, columns', [
    (Gt(Attribute('col1'), 1), {Attribute('col1')}),
    (Ge(Attribute('col2'), 1), {Attribute('col2')}),
    (Lt(Attribute('col3'), 1), {Attribute('col3')}),
    (Le(Attribute('col4'), 1), {Attribute('col4')}),
    (In(Attribute('col5'), [1, 2]), {Attribute('col5')}),
    (Not(In(Attribute('col6'), [3, 4])), {Attribute('col6')}),
    (
        And([Ge(Attribute('col7'), 3), Le(Attribute('col8'), 4)]),
        {Attribute('col7'), Attribute('col8')}),
    (
        Or([In(Attribute('col1'), [3]), In(Attribute('col2'), [4])]),
        {Attribute('col1'), Attribute('col2')}),
    ])
def test_get_attributes(expression, columns):
    assert get_attributes(expression) == columns
