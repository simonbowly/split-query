''' Proper contract test for the function and simplification clauses API. '''

import pytest

from octo_spork.clauses import Ge, Gt, Le, Lt, In, And, Or, Not, simplify


@pytest.mark.parametrize('expression, result', [
    # Simple interval and set expressions are not altered.
    (Ge('col', 1), Ge('col', 1)),
    (Gt('col', 2), Gt('col', 2)),
    (Le('col', 3), Le('col', 3)),
    (Lt('col', 4), Lt('col', 4)),
    (In('col', [1, 2, 3]), In('col', [1, 2, 3])),
    # Inverses map correctly.
    (Not(Ge('col', 5)), Lt('col', 5)),
    (Not(Gt('col', 6)), Le('col', 6)),
    (Not(Le('col', 7)), Gt('col', 7)),
    (Not(Lt('col', 8)), Ge('col', 8)),
    (Not(In('col', [1, 2])), Not(In('col', [1, 2]))),
    # Compound of single expressions.
    (And([Ge('col1', 0)]), Ge('col1', 0)),
    (Or([Lt('col2', 1)]), Lt('col2', 1)),
    # Compound expressions that cannot be simplified.
    (And([Ge('col', 2), Le('col', 5)]), And([Ge('col', 2), Le('col', 5)])),
    (And([Gt('col', 2), Lt('col', 5)]), And([Gt('col', 2), Lt('col', 5)])),
    (Or([Lt('col', 3), Ge('col', 4)]), Or([Lt('col', 3), Ge('col', 4)])),
    (Or([Le('col', 1), Gt('col', 6)]), Or([Le('col', 1), Gt('col', 6)])),
    # Compound reducible interval expressions.
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
    # Compound reducible set expressions.
    (Or([In('col', [1, 2]), In('col', [2, 3])]), In('col', [1, 2, 3])),
    (And([In('col', [1, 2]), In('col', [2, 3])]), In('col', [2])),
    (And([In('col1', [1, 2]), Not(In('col1', [2, 3]))]), In('col1', [1])),
    # Multiple columns/expression types: irreducible.
    (
        Or([In('col1', [1, 2]), In('col2', [1, 2])]),
        Or([In('col1', [1, 2]), In('col2', [1, 2])])),
    (
        And([In('col1', [1, 2]), In('col2', [1, 2])]),
        And([In('col1', [1, 2]), In('col2', [1, 2])])),
    (
        And([Ge('col1', 1), Le('col1', 2), In('col2', [1, 2])]),
        # And([Ge('col1', 1), Le('col1', 2), In('col2', [1, 2])])),
        # Need simple flattener after grouped processing.
        And([Ge('col1', 1), Le('col1', 2), In('col2', [1, 2])])),
    (
        Or([Le('col1', 1), Ge('col1', 2), In('col2', [1, 2])]),
        # Or([Le('col1', 1), Ge('col1', 2), In('col2', [1, 2])])),
        Or([Le('col1', 1), Ge('col1', 2), In('col2', [1, 2])])),
    # Multi-column reducible
    (
        And([In('col1', [1, 2, 3]), In('col1', [2, 3, 4]), In('col2', [5, 6, 7])]),
        And([In('col1', [2, 3]), In('col2', [5, 6, 7])])),
    (
        Or([In('col1', [1, 2, 3]), In('col1', [2, 3, 4]), In('col2', [5, 6, 7]), In('col2', [8, 9])]),
        Or([In('col1', [1, 2, 3, 4]), In('col2', [5, 6, 7, 8, 9])])),
    (
        And([
            And([In('col1', [1, 2, 3]), In('col2', [4, 5, 6])]),
            Not(And([In('col1', [2, 3]), In('col2', [4, 5, 6])]))]),
        And([In('col1', [1]), In('col2', [4, 5, 6])])),
    (
        And([
            And([In('col1', [1, 2, 3]), In('col2', [4, 5, 6])]),
            Not(And([In('col1', [1, 2, 3]), In('col2', [4, 5])]))]),
        And([In('col1', [1, 2, 3]), In('col2', [6])])),
    ])
def test_simplify(expression, result):
    assert simplify(expression) == result
