
import datetime

import pytest

from octo_spork.query import (
    Column, EqualTo, In, And, Or, Range, Not, Query,
    GreaterThan, GreaterThanOrEqualTo, LessThan, LessThanOrEqualTo)
from octo_spork.sql import SQLRepresentor, SQLRepresentationError


col1 = Column('table1', 'column1')
col2 = Column('table1', 'column2')


@pytest.mark.parametrize('obj, expected', [
    (1, "1"),
    (1.2, "1.2"),
    ("loc", "'loc'"),
    (datetime.datetime(2016, 5, 1, 10, 22, 1), "'2016-05-01T10:22:01'"),
    (GreaterThanOrEqualTo(col1, 1), "table1.column1 >= 1"),
    (GreaterThan(col1, 1), "table1.column1 > 1"),
    (LessThanOrEqualTo(col1, 1), "table1.column1 <= 1"),
    (LessThan(col1, 1), "table1.column1 < 1"),
    (Range(col1, 0, 1, True, False), "table1.column1 >= 0 and table1.column1 < 1"),
    (In(col1, [1, 2]), "table1.column1 in (1,2)"),
    (And(['a', 'b']), "('a') and ('b')"),
    (And(['a', 'b', 'c']), "('a') and ('b') and ('c')"),
    (Or(['a', 'b']), "('a') or ('b')"),
    (Or(['a', 'b', 'c']), "('a') or ('b') or ('c')"),
    (EqualTo(col1, 1), "table1.column1 = 1"),
    (Not('a'), "not 'a'"),
    (Not(In(col1, [1, 2])), "not table1.column1 in (1,2)"),
    (
        Query(table='table1', select=[col1, col2], where=EqualTo(col1, 0)),
        "select table1.column1, table1.column2 where table1.column1 = 0")
    # (Between(col1, 1, 2), "table1.column1 between 1 and 2"),
    ])
def test_sql_string(obj, expected):
    assert SQLRepresentor().repr(obj) == expected


@pytest.mark.parametrize('obj, expected', [
    (EqualTo(col1, 1), "name1 = 1"),
    ])
def test_column_sources(obj, expected):
    sql = SQLRepresentor(sources={
        Column('table1', 'column1'): 'name1',
        Column('table1', 'column2'): 'name2'})
    assert sql.repr(obj) == expected


def test_sql_errors():
    with pytest.raises(SQLRepresentationError):
        SQLRepresentor().repr(dict())
