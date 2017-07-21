
import pytest
import sympy as sp

from octo_spork.expressions import And, Or, Not
from octo_spork.reduce_logic import SympyExpressionMapper, flatten


@pytest.mark.parametrize('expression, result', [
    (And(['a', 'b']), sp.And(sp.symbols('x1'), sp.symbols('x2'))),
    (Or(['a', 'b']), sp.Or(sp.symbols('x1'), sp.symbols('x2'))),
    (Not('a'), sp.Not(sp.symbols('x1'))),
    ])
def test_to_sympy(expression, result):
    mapper = SympyExpressionMapper()
    mapped = mapper.to_sympy(expression)
    assert mapped == result
    unmapped = mapper.from_sympy(mapped)
    assert unmapped == expression


@pytest.mark.parametrize('expression', [
    And(['a', 'b', 'c']),
    Or(['c', 'b', 'a']),
    And([Or(['a', 'b']), Not('c')]),
    ])
def test_recover_mapped(expression):
    mapper = SympyExpressionMapper()
    mapped = mapper.to_sympy(expression)
    assert mapper.from_sympy(mapped) == expression


@pytest.mark.parametrize('expression', [
    And(['a', And(['b', 'c'])]),
    Or([Or(['c', 'b']), 'a']),
    And([Or(['a', 'b']), Not('c')]),
    ])
def test_recover_simplified(expression):
    mapper = SympyExpressionMapper()
    mapped1 = mapper.to_sympy(expression)
    mapped2 = mapper.to_sympy(mapper.from_sympy(mapped1))
    assert mapped1 == mapped2


@pytest.mark.parametrize('expression, method, result', [
    (
        And([And(['e1', 'e2']), Not(And(['e1', 'e3']))]), 'dnf',
        And(['e2', 'e1', Not('e3')])),
    (
        And([And(['e1', 'e2']), Not(And(['e1', 'e3']))]), 'cnf',
        And(['e2', 'e1', Not('e3')])),
    (
        And([And(['a', 'b']), Not(And(['c', 'd']))]), 'dnf',
        Or([And([Not('d'), 'b', 'a']), And([Not('c'), 'b', 'a'])])),
    (
        And([And(['a', 'b']), Not(And(['c', 'd']))]), 'cnf',
        And([Or([Not('d'), Not('c')]), 'b', 'a'])),
    ])
def test_flatten(expression, method, result):
    assert flatten(expression, method) == result
