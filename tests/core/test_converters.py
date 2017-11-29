
from datetime import datetime
import functools

import pytest

from split_query.core.converters import convert_expression, substitute_attributes, in_to_or, soql, map_to_ids
from split_query.core.expressions import And, Or, Not, In, Eq, Le, Lt, Ge, Gt, Attribute


a, b, c, x, y, z = [Attribute(n) for n in 'abcxyz']
col1 = Attribute('column1')

TESTCASES_SUBSTITUTE = [
    (a, x),
    (b, y),
    (c, c),
    (Eq(a, 1), Eq(x, 1)),
    (And([Eq(a, 1), Eq(c, 2)]), And([Eq(x, 1), Eq(c, 2)])),
    (Or([Gt(a, 1), Lt(c, 2)]), Or([Gt(x, 1), Lt(c, 2)])),
    (
        And([Or([Le(a, 1), Ge(c, 2)]), Eq(b, 3)]),
        And([Or([Le(x, 1), Ge(c, 2)]), Eq(y, 3)])),
    (Not(In(a, [1, 2, 3])), Not(In(x, [1, 2, 3]))),
]

TESTCASES_IN_TO_OR = [
    (In(x, [1, 2, 3]), Or([Eq(x, 1), Eq(x, 2), Eq(x, 3)])),
    (
        Not(In(x, [1, 2, 3])),
        Not(Or([Eq(x, 1), Eq(x, 2), Eq(x, 3)]))),
]

TESTCASES_SOQL = [
    (1, "1"),
    (1.2, "1.2"),
    ("loc", "'loc'"),
    (datetime(2016, 5, 1, 10, 22, 1), "'2016-05-01T10:22:01'"),
    (Ge(col1, 1), "column1 >= 1"),
    (Gt(col1, 1), "column1 > 1"),
    (Le(col1, 1), "column1 <= 1"),
    (Lt(col1, 1), "column1 < 1"),
    (In(col1, [1, 2]), "column1 in (1,2)"),
    (And(['a', 'b']), "('a') and ('b')"),
    (And(['a', 'b', 'c']), "('a') and ('b') and ('c')"),
    (Or(['a', 'b']), "('a') or ('b')"),
    (Or(['a', 'b', 'c']), "('a') or ('b') or ('c')"),
    (Eq(col1, 1), "column1 = 1"),
    (Not('a'), "not ('a')"),
    (Not(In(col1, [1, 2])), "not (column1 in (1,2))"),
    (
        And([Ge(col1, 0), Lt(col1, 1)]),
        "(column1 < 1) and (column1 >= 0)"),
]

TESTCASES_MAP_TO_IDS = [
    (Eq(x, 'a'), Eq(y, 1)),
    (In(a, ['a', 'b', 'c']), In(b, [4, 5, 6])),
]


@pytest.mark.parametrize('expression, expected', TESTCASES_SUBSTITUTE)
def test_substitute_attributes(expression, expected):
    result = convert_expression(expression, hook=functools.partial(
        substitute_attributes, substitutions={a: x, b: y}))
    assert result == expected


@pytest.mark.parametrize('expression, expected', TESTCASES_IN_TO_OR)
def test_in_to_or(expression, expected):
    result = convert_expression(expression, hook=in_to_or)
    assert result == expected


@pytest.mark.parametrize('expression, expected', TESTCASES_SOQL)
def test_soql(expression, expected):
    result = convert_expression(expression, hook=soql)
    assert result == expected


@pytest.mark.parametrize('expression, expected', TESTCASES_MAP_TO_IDS)
def test_map_to_ids(expression, expected):
    MAP = {
        Attribute('x'): (Attribute('y'), {'a': 1}),
        Attribute('a'): (Attribute('b'), {'a': 4, 'b': 5, 'c': 6}),
    }
    result = convert_expression(expression, hook=functools.partial(
        map_to_ids, attribute_map=MAP))
    assert result == expected
