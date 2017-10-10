
from datetime import datetime

import pytest

from octo_spork.query import (
    Column, Query, EqualTo, In, Range, LessThan, GreaterThan, And)
from octo_spork.pandas_engine import PandasEngine


col1a = Column('table1', 'columna')
col1b = Column('table1', 'columnb')
col1c = Column('table1', 'columnc')

SIMPLE_DATA = [
    dict(columna=1, columnb=2, columnc=3),
    dict(columna=4, columnb=5, columnc=6),
    dict(columna=7, columnb=8, columnc=9)]

TIMESERIES_DATA = [
    dict(columna=datetime(2013, 1, 1, 0, 0, 0), columnb='2013'),
    dict(columna=datetime(2014, 1, 1, 0, 0, 0), columnb='2014'),
    dict(columna=datetime(2015, 1, 1, 0, 0, 0), columnb='2015'),
    dict(columna=datetime(2016, 1, 1, 0, 0, 0), columnb='2016'),
    dict(columna=datetime(2017, 1, 1, 0, 0, 0), columnb='2017'),
]


@pytest.fixture
def engine():
    return PandasEngine()


@pytest.mark.parametrize('testcase', [
    # Column selection.
    dict(
        data=SIMPLE_DATA,
        query=Query(table='table1', select=[col1a, col1b]),
        expected=[
            dict(columna=1, columnb=2),
            dict(columna=4, columnb=5),
            dict(columna=7, columnb=8),
            ]),
    # Discrete value filters.
    dict(
        data=SIMPLE_DATA,
        query=Query(table='table1', select=[col1a, col1b], where=EqualTo(col1a, 1)),
        expected=[
            dict(columna=1, columnb=2)],
            ),
    dict(
        data=SIMPLE_DATA,
        query=Query(table='table1', select=[col1a, col1b], where=In(col1a, [4, 7])),
        expected=[
            dict(columna=4, columnb=5),
            dict(columna=7, columnb=8),
            ]),
    # Muliple filters/logical expressions.
    dict(
        data=SIMPLE_DATA,
        query=Query(
            table='table1', select=[col1a, col1b],
            where=And([In(col1a, [4, 7]), In(col1b, [2, 5])])),
        expected=[
            dict(columna=4, columnb=5),
            ]),
    # Numeric range filters.
    dict(
        data=SIMPLE_DATA,
        query=Query(table='table1', select=[col1a, col1b], where=Range(
                col1b, lower=3, upper=6, incl_lower=False, incl_upper=False)),
        expected=[
            dict(columna=4, columnb=5),
            ]),
    dict(
        data=SIMPLE_DATA,
        query=Query(table='table1', select=[col1a, col1b], where=LessThan(col1b, 6)),
        expected=[
            dict(columna=1, columnb=2),
            dict(columna=4, columnb=5),
            ]),
    dict(
        data=SIMPLE_DATA,
        query=Query(table='table1', select=[col1a, col1b], where=GreaterThan(col1b, 4)),
        expected=[
            dict(columna=4, columnb=5),
            dict(columna=7, columnb=8),
            ]),
    # Datetime range filters.
    dict(
        data=TIMESERIES_DATA,
        query=Query(table='table1', select=[col1a, col1b], where=Range(
                col1a, incl_lower=False, incl_upper=False,
                lower=datetime(2013, 6, 1, 0, 0, 0),
                upper=datetime(2016, 6, 1, 0, 0, 0))),
        expected=[
            dict(columna=datetime(2014, 1, 1, 0, 0, 0), columnb='2014'),
            dict(columna=datetime(2015, 1, 1, 0, 0, 0), columnb='2015'),
            dict(columna=datetime(2016, 1, 1, 0, 0, 0), columnb='2016'),
            ]),
    dict(
        data=TIMESERIES_DATA,
        query=Query(
            table='table1', select=[col1a, col1b],
            where=LessThan(col1a, datetime(2015, 6, 1, 0, 0, 0))),
        expected=[
            dict(columna=datetime(2013, 1, 1, 0, 0, 0), columnb='2013'),
            dict(columna=datetime(2014, 1, 1, 0, 0, 0), columnb='2014'),
            dict(columna=datetime(2015, 1, 1, 0, 0, 0), columnb='2015'),
            ]),
    dict(
        data=TIMESERIES_DATA,
        query=Query(
            table='table1', select=[col1a, col1b],
            where=GreaterThan(col1a, datetime(2015, 6, 1, 0, 0, 0))),
        expected=[
            dict(columna=datetime(2016, 1, 1, 0, 0, 0), columnb='2016'),
            dict(columna=datetime(2017, 1, 1, 0, 0, 0), columnb='2017'),
            ]),
    ])
def test_refine(engine, testcase):
    result = engine.refine(engine.process(testcase['data']), testcase['query'])
    assert result.to_dict() == engine.process(testcase['expected']).to_dict()


def test_union(engine):
    part1 = SIMPLE_DATA
    part2 = [
        dict(columna=-1, columnb=-2, columnc=-3),
        dict(columna=-4, columnb=-5, columnc=-6),
        dict(columna=-7, columnb=-8, columnc=-9)]
    result = engine.union([engine.process(part1), engine.process(part2)])
    assert result.to_dict() == engine.process(part1 + part2).to_dict()
