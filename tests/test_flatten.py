
import pytest

from octo_spork.expressions import Le, Lt, Ge, Gt, And, Or, Not, In
from octo_spork.reduce_logic import flatten


EXPRESSIONS = [
    And([Gt('col1', 1), And([Gt('col2', 2), Gt('col2a', 2), And([Gt('col3', 3), Gt('col4', 4)])])]),
    And([Gt('col1', 1), Gt('col2', 2), Gt('col2a', 2), Gt('col3', 3), Gt('col4', 4)]),
    Or([Gt('col1', 1), Or([Gt('col2', 2), Gt('col2a', 2), Or([Gt('col3', 3), Gt('col4', 4)])])]),
    Or([Gt('col1', 1), Gt('col2', 2), Gt('col2a', 2), Gt('col3', 3), Gt('col4', 4)]),
    And([Gt('col1', 1), And([Gt('col2', 2), Gt('col2a', 2), Or([Gt('col3', 3), Gt('col4', 4)])])]),
    And([Gt('col1', 1), Gt('col2', 2), Gt('col2a', 2), Or([Gt('col3', 3), Gt('col4', 4)])]),
    Or([And([Ge('col1', 1), Or([Le('col2', 3), Le('col2', 2)]), Ge('col1', 2)])]),
    And([Ge('col1', 1), Or([Le('col2', 3), Le('col2', 2)]), Ge('col1', 2)]),
    Ge('col', 1),
    Gt('col', 1),
    Le('col', 1),
    Lt('col', 1),
    In('col', [1, 2, 3]),
    Not(Ge('col', 1)),
    Not(Gt('col', 1)),
    Not(Le('col', 1)),
    Not(Lt('col', 1)),
    Not(In('col', [1, 2, 3])),
    And([Ge('col1', 0)]),
    Or([Lt('col2', 1)]),
    And([Ge('col', 2), Le('col', 5)]),
    And([Gt('col', 2), Lt('col', 5)]),
    Or([Lt('col', 3), Ge('col', 4)]),
    Or([Le('col', 1), Gt('col', 6)]),
    And([Ge('col', 2), Le('col', 7), Le('col', 5)]),
    And([Ge('col', 2), Le('col', 5)]),
    And([Gt('col', 2), Lt('col', 7), Lt('col', 5)]),
    And([Gt('col', 2), Lt('col', 5)]),
    And([
        And([Ge('col', 2), Le('col', 4)]),
        Not(And([Ge('col', 3), Le('col', 4)]))]),
    And([Ge('col', 2), Lt('col', 3)]),
    And([
        And([Ge('col', 2), Le('col', 5)]),
        Not(And([Ge('col', 3), Le('col', 4)]))]),
    Or([
        And([Ge('col', 2), Lt('col', 3)]),
        And([Gt('col', 4), Le('col', 5)])]),
    Or([In('col', [1, 2]), In('col', [2, 3])]),
    And([In('col', [1, 2]), In('col', [2, 3])]),
    And([In('col1', [1, 2]), Not(In('col1', [2, 3]))]),
    Or([In('col1', [1, 2]), In('col2', [1, 2])]),
    And([In('col1', [1, 2]), In('col2', [1, 2])]),
    And([Ge('col1', 1), Le('col1', 2), In('col2', [1, 2])]),
    Or([Le('col1', 1), Ge('col1', 2), In('col2', [1, 2])]),
    And([In('col1', [1, 2, 3]), In('col1', [2, 3, 4]), In('col2', [5, 6, 7])]),
    And([In('col1', [2, 3]), In('col2', [5, 6, 7])]),
    Or([In('col1', [1, 2, 3]), In('col1', [2, 3, 4]), In('col2', [5, 6, 7]), In('col2', [8, 9])]),
    Or([In('col1', [1, 2, 3, 4]), In('col2', [5, 6, 7, 8, 9])]),
    Or([And([
        Ge('col1', 1),
        Or([
            Le('col2', 3),
            Le('col2', 2)]),
        Ge('col1', 2)])]),
    And([Le('col2', 3), Ge('col1', 2)]),
    Or([
        And([
            Ge('col1', 1),
            Or([
                Le('col2', 3),
                Le('col2', 2)]),
            Ge('col1', 2)]),
        Lt('col2', 0),
        Lt('col2', -1)]),
    Or([
        And([Le('col2', 3), Ge('col1', 2)]),
        Lt('col2', 0)]),
    Not(And([In('e1', [1]), In('e2', [2])])),
]


@pytest.mark.parametrize('expression', EXPRESSIONS)
def test_flatten(expression):
    flatten(expression, method='cnf')
    flatten(expression, method='dnf')
