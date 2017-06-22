
import datetime

import pytest

from octo_spork.query import (
    Column, EqualTo, In, And, Or, Range,
    GreaterThan, GreaterThanOrEqualTo, LessThan, LessThanOrEqualTo)
from octo_spork.sql import to_sql, SQLRepresentationError


col1 = Column('table1', 'column1')


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
    # (Between(col1, 1, 2), "table1.column1 between 1 and 2"),
    # (Not('a'), "not 'a'"),
    # (Not(In(col1, [1, 2])), "not table1.column1 in (1,2)"),
    ])
def test_sql_string(obj, expected):
    assert to_sql(obj) == expected


@pytest.mark.parametrize('obj, expected', [
    (Column('table1', 'column1'), "table1.column1 as x"),
    (Column('table1', 'column2'), "table1.column2"),
    (Column('table2', 'column1'), "table2.column1 as y"),
    ])
def test_sql_alias(obj, expected):
    alias = {
        Column('table1', 'column1'): 'x',
        Column('table2', 'column1'): 'y'}
    assert to_sql(obj, alias_map=alias) == expected


def test_sql_errors():
    with pytest.raises(SQLRepresentationError):
        to_sql(col1, alias_map=1)
    with pytest.raises(SQLRepresentationError):
        to_sql(dict())
