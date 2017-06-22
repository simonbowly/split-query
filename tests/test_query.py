''' Query relationship tests. Also verifies any query specifications are
hashable (objects are intended to be immutable). '''

from datetime import datetime

import pytest

from octo_spork.query import (
    Column, EqualTo, In, And, Or, Not, Range,
    GreaterThan, GreaterThanOrEqualTo, LessThan, LessThanOrEqualTo,
    Query, DecompositionError, decompose)


col1a = Column('table1', 'columna')
col1b = Column('table1', 'columnb')
col1c = Column('table1', 'columnc')
col2x = Column('table2', 'columnx')
col2y = Column('table2', 'columny')
col2z = Column('table2', 'columnz')

eq1a = EqualTo(col1a, 1)
eq1b = EqualTo(col1b, 1)
eq1c = EqualTo(col1c, 1)


@pytest.mark.parametrize('testcase', [
    # Identical objects.
    dict(
        query=EqualTo(col1a, 2), source=EqualTo(col1a, 2),
        refine=None, remainder=None),
    # Unfiltered source.
    dict(
        query=EqualTo(col1a, 2), source=None,
        refine=EqualTo(col1a, 2), remainder=None),
    # Superset, refine.
    dict(
        query=In(col1a, [1, 2, 3]), source=In(col1a, [1, 2, 3, 4]),
        refine=In(col1a, [1, 2, 3]), remainder=None),
    # Subset, remainder.
    dict(
        query=In(col1a, [1, 2, 3, 4]), source=In(col1a, [1, 2]),
        refine=None, remainder=In(col1a, [3, 4])),
    # Partial overlap.
    dict(
        query=In(col1a, [1, 2, 3, 4]), source=In(col1a, [3, 4, 5, 6]),
        refine=In(col1a, [3, 4]), remainder=In(col1a, [1, 2])),
    # Larger source ranges requiring refinement.
    dict(
        query=Range(col1a, lower=0, upper=5, incl_lower=True, incl_upper=True),
        source=Range(col1a, lower=-2, upper=5, incl_lower=True, incl_upper=True),
        refine=Range(col1a, lower=0, upper=5, incl_lower=True, incl_upper=True),
        remainder=None),
    dict(
        query=Range(col1a, lower=0, upper=5, incl_lower=True, incl_upper=True),
        source=Range(col1a, lower=0, upper=7, incl_lower=True, incl_upper=True),
        refine=Range(col1a, lower=0, upper=5, incl_lower=True, incl_upper=True),
        remainder=None),
    # Smaller source ranges requiring remainders.
    dict(
        query=Range(col1a, lower=0, upper=5, incl_lower=True, incl_upper=True),
        source=Range(col1a, lower=2, upper=5, incl_lower=False, incl_upper=True),
        refine=None,
        remainder=Range(col1a, lower=0, upper=2, incl_lower=True, incl_upper=True)),
    dict(
        query=Range(col1a, lower=0, upper=5, incl_lower=False, incl_upper=True),
        source=Range(col1a, lower=2, upper=5, incl_lower=True, incl_upper=True),
        refine=None,
        remainder=Range(col1a, lower=0, upper=2, incl_lower=False, incl_upper=False)),
    dict(
        query=Range(col1a, lower=0, upper=5, incl_lower=False, incl_upper=False),
        source=Range(col1a, lower=-1, upper=3, incl_lower=False, incl_upper=False),
        refine=Range(col1a, lower=0, upper=5, incl_lower=False, incl_upper=False),
        remainder=Range(col1a, lower=3, upper=5, incl_lower=True, incl_upper=False)),
    dict(
        query=Range(col1a, lower=0, upper=5, incl_lower=True, incl_upper=False),
        source=Range(col1a, lower=1, upper=4, incl_lower=False, incl_upper=True),
        refine=None, remainder=Or([
            Range(col1a, lower=0, upper=1, incl_lower=True, incl_upper=True),
            Range(col1a, lower=4, upper=5, incl_lower=False, incl_upper=False)])),
    # Convenience functions for ranges.
    dict(
        query=GreaterThan(col1a, 0), source=LessThan(col1a, 1),
        refine=GreaterThan(col1a, 0), remainder=GreaterThanOrEqualTo(col1a, 1)),
    dict(
        query=LessThan(col1a, 10), source=LessThan(col1a, 0), refine=None,
        remainder=Range(col1a, lower=0, upper=10, incl_lower=True, incl_upper=False)),
    # Inverse functions for partial ranges.
    dict(
        query=None, source=GreaterThan(col1a, 0),
        refine=None, remainder=LessThanOrEqualTo(col1a, 0)),
    dict(
        query=None, source=GreaterThanOrEqualTo(col1a, 0),
        refine=None, remainder=LessThan(col1a, 0)),
    dict(
        query=None, source=LessThan(col1a, 0),
        refine=None, remainder=GreaterThanOrEqualTo(col1a, 0)),
    dict(
        query=None, source=LessThanOrEqualTo(col1a, 0),
        refine=None, remainder=GreaterThan(col1a, 0)),
    dict(
        query=None, source=Range(col1a, 0, 1, True, True), refine=None,
        remainder=Or([LessThan(col1a, 0), GreaterThan(col1a, 1)])),
    dict(
        query=None, refine=None,
        source=Range(
            col1a, incl_lower=True, incl_upper=True,
            lower=datetime(2015, 1, 1, 0, 0, 0),
            upper=datetime(2016, 1, 1, 0, 0, 0)),
        remainder=Or([
            LessThan(col1a, datetime(2015, 1, 1, 0, 0, 0)),
            GreaterThan(col1a, datetime(2016, 1, 1, 0, 0, 0))])),
    # Logical compositions
    dict(
        query=And([eq1a, eq1b]), source=And([eq1a, eq1c]),
        refine=eq1b, remainder=And([eq1a, eq1b, Not(eq1c)])),
    dict(
        query=And([eq1a, eq1b]), source=eq1a,
        refine=eq1b, remainder=None),
    dict(
        query=eq1a, source=And([eq1a, eq1b]),
        refine=None, remainder=And([eq1a, Not(eq1b)])),
    # Full query objects
    dict(
        query=Query(table='table1', select=[col1a, col1b, col1c]),
        source=Query(table='table1', select=[col1a, col1b, col1c]),
        refine=None, remainder=None),
    dict(
        query=Query(table='table1', select=[col1a, col1b]),
        source=Query(table='table1', select=[col1a, col1b, col1c]),
        refine=Query(table='table1', select=[col1a, col1b]),
        remainder=None),
    dict(
        query=Query(table='table1', select=[col1a, col1b], where=In(col1a, [1, 2])),
        source=Query(table='table1', select=[col1a, col1b, col1c], where=In(col1a, [1])),
        refine=Query(table='table1', select=[col1a, col1b]),
        remainder=Query(table='table1', select=[col1a, col1b], where=In(col1a, [2]))),
    ])
def test_decompose(testcase):
    assert decompose(testcase['query'], testcase['source']) == (
        testcase['refine'], testcase['remainder'])


@pytest.mark.parametrize('testcase', [
    dict(
        query=Query(table='table1', select=[col1a, col1b, col1c]),
        source=Query(table='table1', select=[col1a, col1b])),
    ])
def test_decompose_error(testcase):
    with pytest.raises(DecompositionError):
        decompose(testcase['query'], testcase['source'])


@pytest.mark.parametrize('query, columns, tables', [
    (Query(table='table1'), set(), {'table1'}),
    (Query(table='table1', select=[col1a]), {col1a}, {'table1'}),
    (Query(table='table1', select=[col1a, col1b]), {col1a, col1b}, {'table1'}),
    (Query(table='table1', select=[col1a, col2x]), {col1a, col2x}, {'table1', 'table2'}),
    (
        Query(table='table1', where=And([In(col1a, [1, 2]), EqualTo(col2x, 0)])),
        {col1a, col2x}, {'table1', 'table2'}),
    (
        Query(table='table1', where=Or([In(col1b, [1, 2]), Range(col2y, 0, 1, True, True)])),
        {col1b, col2y}, {'table1', 'table2'}),
    ])
def test_columns_tables(query, columns, tables):
    hash((query, query.columns, query.tables))
    assert query.columns == columns
    assert query.tables == tables
