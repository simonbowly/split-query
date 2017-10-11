
from hypothesis import given, example
import pytest
import sympy as sp

from .testing import st_expressions
from octo_spork.expressions import And, Or, Not, Lt, Gt, Attribute
from octo_spork.logic import SympyExpressionMapper, to_dnf, to_cnf


@pytest.mark.parametrize('expression, result', [
    (And(['a', 'b']), sp.And(sp.symbols('x1'), sp.symbols('x2'))),
    (Or(['a', 'b']), sp.Or(sp.symbols('x1'), sp.symbols('x2'))),
    (Not('a'), sp.Not(sp.symbols('x1'))),
    (True, True),
    (False, False),
    ])
def test_to_sympy(expression, result):
    ''' Test that the mapper inserts symbols where appropriate recovers the
    original expression. '''
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
    ''' Test that map/recover returns the original expression. Automatic
    simplification means that this is not always the case for certain
    expressions. '''
    mapper = SympyExpressionMapper()
    mapped = mapper.to_sympy(expression)
    assert mapper.from_sympy(mapped) == expression


x1 = Attribute('x1')


@pytest.mark.parametrize('expression, result', [
    (Or([True, Lt(x1, 0)]), True),
    (And([False, Lt(x1, 0)]), False),
    (Or([False, Lt(x1, 0)]), Lt(x1, 0)),
    (And([True, Lt(x1, 0)]), Lt(x1, 0)),
    (Or([False, And([Gt(x1, 0), Lt(x1, 1)])]), And([Gt(x1, 0), Lt(x1, 1)])),
    # (And([True, Lt(x1, 0)]), Lt(x1, 0)),
    ])
def test_literals(expression, result):
    assert to_cnf(expression) == result


# @pytest.mark.parametrize('expression', [
#     And(['a', And(['b', 'c'])]),
#     Or([Or(['c', 'b']), 'a']),
#     And([Or(['a', 'b']), Not('c')]),
#     ])
@given(st_expressions())
def test_recover_simplified(expression):
    ''' Test that sympy representation is consistent when some
    simplification has already occurred. '''
    mapper = SympyExpressionMapper()
    mapped1 = mapper.to_sympy(expression)
    mapped2 = mapper.to_sympy(mapper.from_sympy(mapped1))
    assert mapped1 == mapped2


@pytest.mark.parametrize('expression, result', [
    (
        And([And(['e1', 'e2']), Not(And(['e1', 'e3']))]),
        And(['e2', 'e1', Not('e3')])),
    (
        And([And(['a', 'b']), Not(And(['c', 'd']))]),
        Or([And([Not('d'), 'b', 'a']), And([Not('c'), 'b', 'a'])])),
    ])
def test_to_dnf(expression, result):
    ''' Test expected dnf simplifications. '''
    assert to_dnf(expression) == result


@pytest.mark.parametrize('expression, result', [
    (
        And([And(['e1', 'e2']), Not(And(['e1', 'e3']))]),
        And(['e2', 'e1', Not('e3')])),
    (
        And([And(['a', 'b']), Not(And(['c', 'd']))]),
        And([Or([Not('d'), Not('c')]), 'b', 'a'])),
    ])
def test_to_cnf(expression, result):
    ''' Test expected cnf simplifications. '''
    assert to_cnf(expression) == result


@given(st_expressions(max_leaves=5))
def test_forms(expression):
    ''' Fuzzing error test of the simplification routines.
    TODO test they are the same using an engine implementation? '''
    to_cnf(expression)
    to_dnf(expression)
