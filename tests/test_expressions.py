
import pytest

from octo_spork.expressions import (
    Le, Lt, Ge, Gt, And, Or, Not, In,
    _to_interval, _from_interval, _to_set, _from_set)


def simplify_range(expression):
    ''' This still needs to check columns. '''
    interval = _to_interval(expression)
    return _from_interval('col', interval)


def simplify_set(expression):
    ''' This still needs to check columns. '''
    values = _to_set(expression)
    print(values)
    return _from_set('col', values)


@pytest.mark.parametrize('expression, result', [
    (Ge('col', 1), Ge('col', 1)),
    (Gt('col', 2), Gt('col', 2)),
    (Le('col', 3), Le('col', 3)),
    (Lt('col', 4), Lt('col', 4)),
    (Not(Ge('col', 5)), Lt('col', 5)),
    (Not(Gt('col', 6)), Le('col', 6)),
    (Not(Le('col', 7)), Gt('col', 7)),
    (Not(Lt('col', 8)), Ge('col', 8)),
    (And([Ge('col', 2), Le('col', 5)]), And([Ge('col', 2), Le('col', 5)])),
    (And([Gt('col', 2), Lt('col', 5)]), And([Gt('col', 2), Lt('col', 5)])),
    (Or([Lt('col', 3), Ge('col', 4)]), Or([Lt('col', 3), Ge('col', 4)])),
    (Or([Le('col', 1), Gt('col', 6)]), Or([Le('col', 1), Gt('col', 6)])),
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
def test_simplify_range(expression, result):
    assert simplify_range(expression) == result


@pytest.mark.parametrize('expression, result', [
    (In('col', [1, 2, 3]), In('col', [1, 2, 3])),
    (Or([In('col', [1, 2]), In('col', [2, 3])]), In('col', [1, 2, 3])),
    (And([In('col', [1, 2]), In('col', [2, 3])]), In('col', [2])),
    (Not(In('col', [1, 2])), Not(In('col', [1, 2]))),
    (And([In('col', [1, 2]), Not(In('col', [2, 3]))]), In('col', [1])),
    ])
def test_simplify_set(expression, result):
    assert simplify_set(expression) == result
