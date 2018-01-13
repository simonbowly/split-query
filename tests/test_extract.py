
import pytest

from split_query.core import Attribute, And, In, Ge, Le, Lt, Gt, Not
from split_query.extract import extract_parameters, with_only_fields, split_parameters


XVAR = Attribute('x')
YVAR = Attribute('y')

TESTCASES_EXTRACT = [
    (
        In(XVAR, [1, 2, 3]),
        [dict(attr='x', type='tag', key='xtags', single=False)],
        [(In(XVAR, [1, 2, 3]), dict(xtags={1, 2, 3}))]),
    (
        And([In(XVAR, [1, 2, 3]), Ge(YVAR, 2), Le(YVAR, 4)]),
        [
            dict(attr='x', type='tag', key='xtags', single=False),
            dict(attr='y', type='range', key_lower='from_y', key_upper='to_y')],
        [(And([In(XVAR, [1, 2, 3]), Ge(YVAR, 2), Le(YVAR, 4)]), dict(xtags={1, 2, 3}, from_y=2, to_y=4))]),
    (
        And([In(XVAR, [1, 2, 3]), In(YVAR, [4, 5, 6])]),
        [
            dict(attr='x', type='tag', key='xtag', single=True),
            dict(attr='y', type='tag', key='ytags', single=False)],
        [
            (And([In(XVAR, [1]), In(YVAR, [4, 5, 6])]), dict(xtag=1, ytags={4, 5, 6})),
            (And([In(XVAR, [2]), In(YVAR, [4, 5, 6])]), dict(xtag=2, ytags={4, 5, 6})),
            (And([In(XVAR, [3]), In(YVAR, [4, 5, 6])]), dict(xtag=3, ytags={4, 5, 6})),
            ]),
    ]


@pytest.mark.parametrize('expression, parameters, expected', TESTCASES_EXTRACT)
def test_extract_parameters(expression, parameters, expected):
    result = extract_parameters(expression, parameters)
    assert result == expected


A = Attribute('a')
B = Attribute('b')


@pytest.mark.parametrize('expression, only, result', [
    (And([Lt(A, 2), Gt(B, 3)]), [], True),
    (And([Lt(A, 2), Gt(B, 3)]), ['a'], Lt(A, 2)),
    (And([Lt(A, 2), Gt(B, 3)]), ['b'], Gt(B, 3)),
    (And([Lt(A, 2), Gt(B, 3)]), ['a', 'b', 'c'], And([Lt(A, 2), Gt(B, 3)])),
    ])
def test_with_only_fields(expression, only, result):
    assert with_only_fields(expression, only) == result


TESTCASES_SPLIT = [
    (
        And([
            And([Ge(XVAR, 0), Le(XVAR, 3)]),
            Not(And([Ge(XVAR, 1), Le(XVAR, 2)]))]),
        [dict(attr='x', type='range', key_lower='xl', key_upper='xu')],
        [
            (And([Ge(XVAR, 0), Le(XVAR, 1)]), dict(xl=0, xu=1)),
            (And([Ge(XVAR, 2), Le(XVAR, 3)]), dict(xl=2, xu=3))])
]

@pytest.mark.parametrize('expression, parameters, expected', TESTCASES_SPLIT)
def test_split_parameters(expression, parameters, expected):
    result = split_parameters(expression, parameters)
    result = sorted(result, key=lambda elem: elem[1]['xl'])
    assert list(result) == expected
