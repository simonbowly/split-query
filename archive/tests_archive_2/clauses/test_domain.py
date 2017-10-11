
import pytest

from octo_spork.clauses.functions import Le, Lt, Ge, Gt, In, And, Or, Not
from octo_spork.clauses.domain import simplify_sets, simplify_intervals


@pytest.mark.parametrize('expression, result', [
    # Simple interval and set expressions are not altered.
    (Ge('col', 1), Ge('col', 1)),
    (Gt('col', 2), Gt('col', 2)),
    (Le('col', 3), Le('col', 3)),
    (Lt('col', 4), Lt('col', 4)),
    # # Inverses map correctly.
    (Not(Ge('col', 5)), Lt('col', 5)),
    (Not(Gt('col', 6)), Le('col', 6)),
    (Not(Le('col', 7)), Gt('col', 7)),
    (Not(Lt('col', 8)), Ge('col', 8)),
    # # Compound of single expressions.
    (And([Ge('col1', 0)]), Ge('col1', 0)),
    (Or([Lt('col2', 1)]), Lt('col2', 1)),
    # # Compound expressions that cannot be simplified.
    (And([Ge('col', 2), Le('col', 5)]), And([Ge('col', 2), Le('col', 5)])),
    (And([Gt('col', 2), Lt('col', 5)]), And([Gt('col', 2), Lt('col', 5)])),
    (Or([Lt('col', 3), Ge('col', 4)]), Or([Lt('col', 3), Ge('col', 4)])),
    (Or([Le('col', 1), Gt('col', 6)]), Or([Le('col', 1), Gt('col', 6)])),
    # # Compound reducible interval expressions.
    (
        And([Ge('col', 2), Le('col', 7), Le('col', 5)]),
        And([Ge('col', 2), Le('col', 5)])),
    (
        And([Gt('col', 2), Lt('col', 7), Lt('col', 5)]),
        And([Gt('col', 2), Lt('col', 5)])),
    (
        And([
            And([Ge('col', 2), Le('col', 4)]),
            Not(And([Ge('col', 3), Le('col', 4)]))]),
        And([Ge('col', 2), Lt('col', 3)])),
    (
        And([
            And([Ge('col', 2), Le('col', 5)]),
            Not(And([Ge('col', 3), Le('col', 4)]))]),
        Or([
            And([Ge('col', 2), Lt('col', 3)]),
            And([Gt('col', 4), Le('col', 5)])])),
])
def test_simplify_intervals(expression, result):
    assert simplify_intervals(expression) == result


@pytest.mark.parametrize('expression, result', [
    # Irreducible
    (In('col', [1, 2, 3]), In('col', [1, 2, 3])),
    (Not(In('col', [1, 2])), Not(In('col', [1, 2]))),
    # Reducible
    (Or([In('col', [1, 2]), In('col', [2, 3])]), In('col', [1, 2, 3])),
    (And([In('col', [1, 2]), In('col', [2, 3])]), In('col', [2])),
    (And([In('col1', [1, 2]), Not(In('col1', [2, 3]))]), In('col1', [1])),
])
def test_simplify_sets(expression, result):
    assert simplify_sets(expression) == result
