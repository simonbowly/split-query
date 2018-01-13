''' Test the generic traversal method and functions which return information
about an expression by traversal. '''

import mock
import pytest

from split_query.core import (
    And, Attribute, Eq, Ge, Le, Gt, Lt, In, Not, Or,
    get_attributes, get_clauses, traverse_expression)


RV = 'out'
X, Y, Z = [Attribute(n) for n in 'xyz']
ASSIGNMENTS = {'a': True, 'b': False, 'c': True}


@pytest.mark.parametrize('expression, hook_calls', [
    (Attribute('x'),            {Attribute('x')}),
    (Eq(Attribute('x'), 0),     {Attribute('x'), 0, Eq(RV, RV)}),
    (Ge('x', 0),                {'x', 0, Ge(RV, RV)}),
    (In('y', [0, 1, 2]),        {'y', 0, 1, 2, In(RV, [RV])}),
    (And(['a', 'b', 'c']),      {'a', 'b', 'c', And(['out'])}),
    (Or(['a', 'b', 'c']),       {'a', 'b', 'c', Or(['out'])}),
    (Not('x'),                  {'x', Not(RV)}),
])
def test_traverse_expression(expression, hook_calls):
    ''' Test recursion patterns, ensuring the hook method is called on the way
    back up the tree. '''
    hook = mock.Mock(return_value=RV)
    result = traverse_expression(expression, hook=hook)
    assert result == RV
    assert hook_calls == {call[0][0] for call in hook.call_args_list}


@pytest.mark.parametrize('expression, columns', [
    (True,                          set()),
    (False,                         set()),
    (Eq(X, 1),                      {X}),
    (Not(In(Y, [1, 2, 3])),         {Y}),
    (And([Ge(X, 3), Le(Y, 4)]),     {X, Y}),
    (And([Gt(Y, 3), Lt(Z, 4)]),     {Y, Z}),
])
def test_get_attributes(expression, columns):
    assert get_attributes(expression) == columns


@pytest.mark.parametrize('expression, clauses', [
    ('a',                           {'a'}),
    (And(['a', 'b']),               {'a', 'b'}),
    (And(['a', Not('b')]),          {'a', 'b'}),
    (Or(['a', 'c']),                {'a', 'c'}),
    (Not(Or(['a', 'c'])),           {'a', 'c'}),
    (And(['a', Not('b'), True]),    {'a', 'b'}),
    (And(['a', Not('c'), False]),   {'a', 'c'}),
])
def test_get_clauses(expression, clauses):
    assert get_clauses(expression) == clauses
