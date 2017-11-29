
import pytest
from frozendict import frozendict
from hypothesis import strategies as st
from hypothesis import assume, event, given

from split_query.core.expressions import And, Not, Or
from split_query.core.truth_table import (expand_dnf, get_clauses, substitute,
                                     truth_table)

from .strategies import expressions, float_expressions

TESTCASES_GET_CLAUSES = [
    ('a',                           {'a'}),
    (And(['a', 'b']),               {'a', 'b'}),
    (And(['a', Not('b')]),          {'a', 'b'}),
    (Or(['a', 'c']),                {'a', 'c'}),
    (Not(Or(['a', 'c'])),           {'a', 'c'}),
    (And(['a', Not('b'), True]),    {'a', 'b'}),
    (And(['a', Not('c'), False]),   {'a', 'c'}),
]


@pytest.mark.parametrize('expression, clauses', TESTCASES_GET_CLAUSES)
def test_get_clauses(expression, clauses):
    assert get_clauses(expression) == clauses


TESTCASES_SUBSTITUTE = [
    ('a',                           True),
    (And(['a', 'b']),               And([True, False])),
    (Or(['a', 'b']),                Or([True, False])),
    (Or(['a', 'c']),                Or([True])),
    (Or(['a', Not('c')]),           Or([True, Not(True)])),
    (Or(['a', Not('c'), False]),    Or([True, Not(True), False])),
    (And(['a', Not('c'), True]),    And([True, Not(True), True])),
]

ASSIGNMENTS = {'a': True, 'b': False, 'c': True}


@pytest.mark.parametrize('expression, result', TESTCASES_SUBSTITUTE)
def test_substitute(expression, result):
    assert substitute(expression, ASSIGNMENTS) == result


TESTCASES_TRUTH_TABLE = [
    (And(['a', 'b']), [
        (dict(a=True, b=True), True),
        (dict(a=True, b=False), False),
        (dict(a=False, b=True), False),
        (dict(a=False, b=False), False),]),
    (Or(['a', 'b']), [
        (dict(a=True, b=True), True),
        (dict(a=True, b=False), True),
        (dict(a=False, b=True), True),
        (dict(a=False, b=False), False),]),
    (
        And(['a', Not('a')]), [
        (dict(a=True), False),
        (dict(a=False), False),]),
    (
        Or(['a', Not('a')]), [
        (dict(a=True), True),
        (dict(a=False), True),]),
]


@pytest.mark.parametrize('expression, expected', TESTCASES_TRUTH_TABLE)
def test_truth_table(expression, expected):
    result = {
        frozendict(assignments): result
        for assignments, result in truth_table(expression)}
    expected = {
        frozendict(assignments): result
        for assignments, result in expected}
    assert result == expected


TESTCASES_EXPAND_DNF = [
    (And(['a', 'b']), Or([And(['a', 'b'])])),
    (Or(['a', 'b']), Or([
        And(['a', 'b']), And([Not('a'), 'b']), And(['a', Not('b')])])),
    (And(['a', Not('a')]),                          False),
    (And([And(['a', 'b']), Not(And(['a', 'b']))]),  False),
    (Or(['a', Not('a')]),                           True),
    (Or([And(['a', 'b']), Not(And(['a', 'b']))]),   True),
]


@pytest.mark.parametrize('expression, result', TESTCASES_EXPAND_DNF)
def test_expand_dnf(expression, result):
    assert expand_dnf(expression) == result


@given(
    expressions(st.one_of(st.just(n) for n in 'xyz'), max_leaves=100) |
    float_expressions('xyz', literals=True, max_leaves=100))
def test_expand_dnf_fuzz(expression):
    ''' Test truth table expansions on expressions with a limited number
    of clauses. '''
    assume(len(get_clauses(expression)) < 6)
    result = expand_dnf(expression)
