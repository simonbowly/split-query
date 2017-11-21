
from datetime import datetime, timedelta

from dateutil.parser import parse as dt_parse

from opendata.socrata_api import SocrataTable
from opendata.paging_mixin import PagingMixin

from octo_spork.query import Range, And, Or, Column, Query, decompose, In, EqualTo
from octo_spork.resolution_tree import DataSources, create_tree, run_tree
from octo_spork.pandas_engine import PandasEngine
from octo_spork.sql import SQLRepresentor


class SocrataRepresentor(SQLRepresentor):

    def repr_select(self, col):
        if self.repr(col) == col.name:
            return col.name
        return '{} as {}'.format(self.repr(col), col.name)

    def repr(self, obj):
        if type(obj) is Query:
            return dict(
                select=', '.join(map(self.repr_select, obj.select)),
                where=self.repr(obj.where))
        if type(obj) is In:
            return super().repr(Or(EqualTo(obj.column, value) for value in obj.valueset))
        return super().repr(obj)


class PedestrianSource(PagingMixin, SocrataTable):

    def __init__(self):
        super().__init__('data.melbourne.vic.gov.au', 'cb85-mn2u')

    def adjust_filters(self, where):
        ''' Logical expression recursion, replacing any range expressions
        on the datetime column where required to round to the nearest year. '''
        if type(where) is And:
            return And(map(self.adjust_filters, where.expressions))
        if type(where) is Or:
            return Or(map(self.adjust_filters, where.expressions))
        if type(where) is Range and where.column == Column('counts', 'datetime'):
            start_year = where.lower.year
            if where.incl_upper:
                end_year = where.upper.year + 1
            else:
                end_year = (where.upper - timedelta(microseconds=1)).year + 1
            return Range(
                where.column, incl_lower=True, incl_upper=False,
                lower=datetime(start_year, 1, 1, 0, 0, 0),
                upper=datetime(end_year, 1, 1, 0, 0, 0))
        return where

    def adjust_query(self, where):
        ''' Logical expression recursion, replacing any range expressions
        on the datetime column with year value ranges. '''
        if type(where) is And:
            return And(map(self.adjust_query, where.expressions))
        if type(where) is Or:
            return Or(map(self.adjust_query, where.expressions))
        if type(where) is Range and where.column == Column('counts', 'datetime'):
            return Range(
                Column('counts', 'year'),
                lower=where.lower.year, upper=where.upper.year,
                incl_lower=True, incl_upper=False)
        return where

    def capability(self, query):
        source = Query(
            table='counts', where=self.adjust_filters(query.where),
            select=[
                Column('counts', 'sensor_id'),
                Column('counts', 'datetime'),
                Column('counts', 'hourly_count'),
                ])
        refine, remainder = decompose(query, source)
        return source, refine, remainder

    def coerce_types(self, entry):
        return dict(
            datetime=dt_parse(entry['datetime']),
            sensor_id=entry['sensor_id'],
            hourly_count=int(entry['hourly_count']))

    def query(self, query):
        soql = SocrataRepresentor(sources={
            Column('counts', 'sensor_id'): 'sensor_id',
            Column('counts', 'datetime'): 'daet_time',
            Column('counts', 'hourly_count'): 'qv_market_peel_st',
            Column('counts', 'year'): 'year'})
        query = Query(table=query.table, select=query.select, where=self.adjust_query(query.where))
        return list(map(self.coerce_types, self.get(**soql.repr(query))))


sources = DataSources(
        source_order=['counts'],
        source_map={'counts': PedestrianSource()},
        source_tables={'counts': {'counts'}})

columns = [
    Column('counts', 'sensor_id'),
    Column('counts', 'datetime'),
    Column('counts', 'hourly_count')]
