
from hypothesis import given, seed
import pytest

from .testing import st_expressions
from octo_spork.expressions import (
    Attribute, Le, Lt, Ge, Gt, And, Or, Not)
from octo_spork.simplify import simplify


x1, x2, x3 = [Attribute('x{}'.format(i+1)) for i in range(3)]


@pytest.mark.parametrize('expression, result', [
    (Le(x1, 2), Le(x1, 2)),
    (And([Ge(x1, 1), Le(x1, 2)]), And([Ge(x1, 1), Le(x1, 2)])),
    (And([Le(x1, 1), Ge(x1, 2)]), False),
    (Or([Ge(x1, 0), Le(x1, 1)]), True),
    (
        And([Ge(x1, 1), Le(x1, 2), Ge(x2, 1), Le(x2, 2)]),
        And([Ge(x1, 1), Le(x1, 2), Ge(x2, 1), Le(x2, 2)])),
    (
        And([Ge(x1, 1), Ge(x1, 2), Ge(x2, 1), Ge(x2, 2)]),
        And([Ge(x1, 2), Ge(x2, 2)])),
    (And([Ge(x1, 1), Le(x2, 2)]), And([Ge(x1, 1), Le(x2, 2)])),
    (
        And([And([Ge(x1, 1), Le(x2, 2)])]),
        And([Ge(x1, 1), Le(x2, 2)])),
    (
        And([Ge(x1, 1), And([Ge(x2, 2), Ge(x3, 3)])]),
        And([Ge(x1, 1), Ge(x2, 2), Ge(x3, 3)])),
    (
        Or([Ge(x1, 1), Or([Ge(x2, 2), Ge(x3, 3)])]),
        Or([Ge(x1, 1), Ge(x2, 2), Ge(x3, 3)])),
    (Not(Ge(x1, 1)), Lt(x1, 1)),
    (
        Not(And([Ge(x1, 1), Ge(x2, 1), Ge(x2, 2)])),
        Not(And([Ge(x1, 1), Ge(x2, 2)]))),
    ])
def test_simplify(expression, result):
    assert simplify(expression) == result


@given(st_expressions())
def test_simplify_fuzz(expression):
    simplify(expression)
