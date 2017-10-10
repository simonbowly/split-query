
import pytest

from octo_spork.clauses.functions import (
    typedtuple, Column, Le, Lt, Ge, Gt, In, And, Or, Not,
    get_categories, get_columns, get_kinds)


Type1 = typedtuple('Type1', ['value1', 'value2'])
Type2 = typedtuple('Type2', ['value1', 'value2'])


def test_equals():
    ''' Identically structured objects of different types are considered unequal. '''
    assert Type1(1, 2) == Type1(1, 2)
    assert Type1(1, 2) != Type1(1, 3)
    assert Type1(1, 2) != Type2(1, 2)
    assert Type2(1, 2) != Type1(1, 2)
    assert not Type1(1, 2) == Type2(1, 2)
    assert not Type2(1, 2) == Type1(1, 2)


def test_hashing():
    ''' Identically structured objects of different types have different hashes. '''
    assert hash(Type1(1, 2)) == hash(Type1(1, 2))
    assert hash(Type1(1, 2)) != hash(Type1(1, 3))
    assert hash(Type1(1, 2)) != hash(Type2(1, 2))
    assert hash(Type2(1, 2)) != hash(Type1(1, 2))


@pytest.mark.parametrize('expression1, expression2', [
    (Column('table1', 'column1'), Column('table1', 'column2')),
    (Le('col1', 1), Lt('col1', 2)),
    (Ge('col1', 3), Gt('col1', 4)),
    (In('col1', [1, 2, 3]), In('col1', [-1, 2, 3])),
    (And(['e1', 'e2', 'e3']), And(['e1', 'e2', 'e4'])),
    (Or(['e1', 'e2', 'e3']), And(['e1', 'e2', 'e3'])),
    (Not(And(['e1', 'e2'])), Not(And(['e1', 'e3']))),
    ])
def test_comparable_expressions(expression1, expression2):
    assert expression1 != expression2
    assert hash(expression1) != hash(expression2)


@pytest.mark.parametrize('expression, columns', [
    (Gt('col1', 1), {'col1'}),
    (Ge('col2', 1), {'col2'}),
    (Lt('col3', 1), {'col3'}),
    (Le('col4', 1), {'col4'}),
    (In('col5', [1, 2]), {'col5'}),
    (Not(In('col6', [3, 4])), {'col6'}),
    (And([Ge('col7', 3), Le('col8', 4)]), {'col7', 'col8'}),
    (Or([In('col1', [3]), In('col2', [4])]), {'col1', 'col2'}),
    ])
def test_get_columns(expression, columns):
    assert get_columns(expression) == columns


@pytest.mark.parametrize('expression, kinds', [
    (Gt('col1', 1), {'interval'}),
    (Ge('col2', 1), {'interval'}),
    (Lt('col3', 1), {'interval'}),
    (Le('col4', 1), {'interval'}),
    (In('col5', [1, 2]), {'set'}),
    (Not(In('col6', [3, 4])), {'set'}),
    (And([Ge('col7', 3), Le('col8', 4)]), {'interval'}),
    (Or([In('col1', [3]), In('col2', [4])]), {'set'}),
    (Or([In('col1', [3]), Ge('col2', 4)]), {'set', 'interval'}), 
    ])
def test_get_kinds(expression, kinds):
    assert get_kinds(expression) == kinds


@pytest.mark.parametrize('expression, kinds', [
    (Gt('col1', 1), {('col1', 'interval')}),
    (Ge('col2', 1), {('col2', 'interval')}),
    (Lt('col3', 1), {('col3', 'interval')}),
    (Le('col4', 1), {('col4', 'interval')}),
    (In('col5', [1, 2]), {('col5', 'set')}),
    (Not(In('col6', [3, 4])), {('col6', 'set')}),
    (And([Ge('col7', 3), Le('col8', 4)]), {('col7', 'interval'), ('col8', 'interval')}),
    (Or([In('col1', [3]), In('col2', [4])]), {('col1', 'set'), ('col2', 'set')}),
    (Or([In('col1', [3]), Ge('col2', 4)]), {('col1', 'set'), ('col2', 'interval')}),
    ])
def test_get_categories(expression, kinds):
    assert get_categories(expression) == kinds
