
from datetime import datetime

import pytest

from octo_spork.query import Column, Range, And, In, Or, Query
from .pedestrians import PedestrianSource


original_filter = Range(
    Column('counts', 'datetime'),
    lower=datetime(2015, 4, 1, 0, 0, 0),
    upper=datetime(2016, 8, 1, 0, 0, 0),
    incl_lower=True, incl_upper=True)

edge_filter = Range(
    Column('counts', 'datetime'),
    lower=datetime(2015, 4, 1, 0, 0, 0),
    upper=datetime(2017, 1, 1, 0, 0, 0),
    incl_lower=True, incl_upper=False)

expanded_filter = Range(
    Column('counts', 'datetime'),
    lower=datetime(2015, 1, 1, 0, 0, 0),
    upper=datetime(2017, 1, 1, 0, 0, 0),
    incl_lower=True, incl_upper=False)

other_filter = In(Column('counts', 'sensor_id'), [1, 2, 3])


@pytest.mark.parametrize('where, expected', [
    (edge_filter, expanded_filter),
    (original_filter, expanded_filter),
    (
        And([original_filter, other_filter]),
        And([expanded_filter, other_filter])),
    (
        Or([original_filter, other_filter]),
        Or([expanded_filter, other_filter])),
    ])
def test_adjust_filters(where, expected):
    assert PedestrianSource().adjust_filters(where) == expected


def test_capability():
    query = Query(
        table='counts', select=[
            Column('counts', 'sensor_id'),
            Column('counts', 'datetime'),
            Column('counts', 'hourly_count')],
        where=And([original_filter, other_filter]))
    source_query, refine, remainder = PedestrianSource().capability(query)

    assert source_query == Query(table='counts', select=query.select, where=And([expanded_filter, other_filter]))
    assert refine == Query(table='counts', select=query.select, where=original_filter)
    assert remainder is None
