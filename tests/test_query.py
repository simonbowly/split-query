''' Query relationship tests. Also verifies any query specifications are
hashable (objects are intended to be immutable). '''

import pytest

from octo_spork.query import (
    Column, In, And, Between, Or, Not,
    GE, GT, LE, LT,
    Query, DecompositionError,
    decompose_where, decompose_select)


col1 = Column('table1', 'column1')
col2 = Column('table1', 'column2')
col3 = Column('table1', 'column3')
col4 = Column('table4', 'column4')
col5 = Column('table5', 'column5')
col6 = Column('table6', 'column6')


@pytest.mark.parametrize('query, source, refine, remainder', [
    # Value set constraints for single column.
    (In(col1, [1, 2]), None, In(col1, [1, 2]), None),
    (In(col1, [1]), In(col1, [1, 2]), In(col1, [1]), None),
    (In(col1, [1, 2]), In(col1, [1]), None, In(col1, [2])),
    (In(col1, [1, 2]), In(col1, [1, 3]), In(col1, [1]), In(col1, [2])),
    # AND composition: refinements required on supersets.
    (And(['e1']), 'e1', None, None),
    (And(['e1', 'e2']), And(['e1', 'e2']), None, None),
    (And(['e1', 'e2']), 'e1', 'e2', None),
    (And(['e1', 'e2', 'e3']), And(['e1', 'e2']), 'e3', None),
    # OR composition: remainders required on subsets.
    (Or(['e1']), 'e1', None, None),
    (Or(['e1', 'e2']), Or(['e1', 'e2']), None, None),
    (Or(['e1', 'e2']), 'e1', None, 'e2'),   # Should be NOT in remainder
    (Or(['e1', 'e2', 'e3']), Or(['e1', 'e2']), None, 'e3'),     # Should be not in remainder
    # Range expressions.
    (Between(col1, 0, 5), Between(col1, 0, 5), None, None),
    (Between(col1, 0, 5), Between(col1, -2, 5), Between(col1, 0, 5), None),
    (Between(col1, 0, 5), Between(col1, 0, 7), Between(col1, 0, 5), None),
    (Between(col1, 0, 5), Between(col1, -2, 7), Between(col1, 0, 5), None),
    (Between(col1, 0, 5), Between(col1, 2, 5), None, Between(col1, 0, 2)),
    (Between(col1, 0, 5), Between(col1, 0, 3), None, Between(col1, 3, 5)),
    (Between(col1, 0, 5), Between(col1, 2, 7), Between(col1, 0, 5), Between(col1, 0, 2)),
    (Between(col1, 0, 5), Between(col1, -2, 3), Between(col1, 0, 5), Between(col1, 3, 5)),
    (Between(col1, 0, 5), Between(col1, 1, 4), None, Or([Between(col1, 0, 1), Between(col1, 4, 5)])),
    # Partial results of full query.
    (None, In(col1, [1, 2]), None, Not(In(col1, [1, 2]))),
    (None, GE(col1, 1), None, LT(col1, 1)),
    (None, GT(col1, 1), None, LE(col1, 1)),
    (None, LE(col1, 1), None, GT(col1, 1)),
    (None, LT(col1, 1), None, GE(col1, 1)),
    ])
def test_decompose_where(query, source, refine, remainder):
    hash((query, source, refine, remainder))
    assert decompose_where(query, source) == (refine, remainder)


@pytest.mark.parametrize('query, source', [
    (And(['e1', 'e2']), And(['e1', 'e2', 'e3'])),
    (Or(['e1', 'e2']), Or(['e1', 'e2', 'e3'])),
    (In(col1, [1, 2]), In(col2, [3, 4])),
    (Between(col1, 0, 1), Between(col2, 0, 2)),
    ])
def test_decompose_where_error(query, source):
    hash((query, source))
    with pytest.raises(DecompositionError):
        decompose_where(query, source)


@pytest.mark.parametrize('query, source, refine', [
    ([col1, col2], [col1, col2], None),
    ([col1, col2], [col1, col2, col3], [col1, col2]),
    ])
def test_decompose_select(query, source, refine):
    refine = refine if refine is None else frozenset(refine)
    assert decompose_select(frozenset(query), frozenset(source)) == refine


@pytest.mark.parametrize('query, source', [
    ([col1, col2], [col1]),
    ])
def test_decompose_select_error(query, source):
    with pytest.raises(DecompositionError):
        decompose_select(frozenset(query), frozenset(source))


@pytest.mark.parametrize('query, columns, tables', [
    (Query(table='table1'), set(), {'table1'}),
    (Query(table='table1', select=[col1]), {col1}, {'table1'}),
    (Query(table='table1', select=[col1, col2]), {col1, col2}, {'table1'}),
    (Query(table='table1', select=[col1, col4]), {col1, col4}, {'table1', 'table4'}),
    (
        Query(table='table1', where=And([In(col1, [1, 2]), Between(col4, 0, 1)])),
        {col1, col4}, {'table1', 'table4'}),
    (
        Query(table='table1', where=Or([In(col1, [1, 2]), Between(col4, 0, 1)])),
        {col1, col4}, {'table1', 'table4'}),
    ])
def test_columns_tables(query, columns, tables):
    hash((query, query.columns, query.tables))
    assert query.columns == columns
    assert query.tables == tables
