
from future.standard_library import install_aliases
install_aliases()

import functools
import itertools
from datetime import datetime
import logging
import urllib

import pandas as pd

from split_query.core import (And, Attribute, Eq, In, Le, Lt, Ge, Gt,
                              simplify_domain, traverse_expression)

from common import cache_persistent, dataset


URL_TEMPLATE = 'http://stat-computing.org/dataexpo/2009/{}.csv.bz2'

COLUMNS = [
    'Date', 'DepTime', 'CRSDepTime', 'ArrTime', 'CRSArrTime', 'UniqueCarrier',
    'FlightNum', 'TailNum', 'ActualElapsedTime', 'CRSElapsedTime',
    'AirTime', 'ArrDelay', 'DepDelay', 'Origin', 'Dest', 'Distance',
    'TaxiIn', 'TaxiOut', 'Cancelled', 'CancellationCode', 'Diverted',
    'CarrierDelay', 'WeatherDelay', 'NASDelay', 'SecurityDelay',
    'LateAircraftDelay']


def read_chunks_grouped(file_name, grouper, **read_kwargs):
    ''' Break up reading large file by month. Requires ordered data. '''
    for chunk in pd.read_csv(file_name, **read_kwargs):
        for group in sorted(chunk.groupby(grouper)):
            yield group


def read_by_group(file_name, grouper, **read_kwargs):
    ''' Read file in chunks, returning a generator of groups produced by
    grouper. Returns the equivalent of
    read_csv(file_name).groupby(grouper).groups, but requires that the groups
    appear in order (for memory reasons). '''
    current_month, current_df = None, None
    logging.info('Reading: {}'.format(file_name))
    for month, df in read_chunks_grouped(file_name, grouper, **read_kwargs):
        if current_month is None:
            current_month, current_df = month, [df]
        else:
            assert month >= current_month
            if month == current_month:
                current_df.append(df)
            else:
                yield current_month, pd.concat(current_df)
                current_month, current_df = month, [df]
    yield current_month, pd.concat(current_df)


def map_parts(iterable):
    for (year, month), df in iterable:
        df['Date'] = pd.to_datetime(df[['Year', 'Month', 'DayofMonth']].rename(
            columns={'DayofMonth': 'Day'}))
        start = datetime(year, month, 1)
        end = (start + pd.tseries.offsets.MonthBegin()).to_pydatetime()
        expression = And([
            Ge(Attribute('Date'), start), Lt(Attribute('Date'), end)])
        logging.info('Partial: {} -> {}'.format(start, end))
        yield expression, df[COLUMNS]


def download_tmp(remote_file):
    logging.info('Loading: {}'.format(remote_file))
    file_name, message = urllib.request.urlretrieve(remote_file)
    return file_name


def get_years(years):
    return map_parts(itertools.chain(*(
        read_by_group(
            download_tmp(URL_TEMPLATE.format(year)),
            grouper=['Year', 'Month'], compression='bz2', chunksize=100000)
        for year in years)))


def _filter_year_only(obj):
    if any(isinstance(obj, cls) for cls in [Eq, In, Le, Lt, Ge, Gt]):
        if obj.attribute == Attribute('Date'):
            if isinstance(obj, Gt) or isinstance(obj, Ge):
                return Ge(Attribute('year'), obj.value.year)
            if isinstance(obj, Lt) or isinstance(obj, Le):
                return Le(Attribute('year'), obj.value.year)
            return obj
        else:
            return True
    return obj


def expr_to_years(expression):
    year_expr = simplify_domain(traverse_expression(
        expression, hook=_filter_year_only))
    _intersections = (
        simplify_domain(And([year_expr, Eq(Attribute('year'), year)]))
        for year in range(1987, 2009))
    return [int(obj.value) for obj in _intersections if obj is not False]


@dataset(name='How Late Are My Airlines', attributes=COLUMNS)
@cache_persistent('airline-data')
class AirlineData(object):
    ''' Airlines!! '''

    def get(self, expression):
        ''' Returns the required superset query in parts iterator. '''
        return get_years(expr_to_years(expression))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    arrivals = AirlineData()
    filtered = arrivals[
        arrivals.UniqueCarrier.isin(['US', 'WN']) &
        arrivals.Date.between(datetime(1987, 11, 2), datetime(1987, 11, 7))]
    print(filtered.get().shape)
    print(filtered.get().Date.min())
    print(filtered.get().Date.max())
    print(filtered.get().UniqueCarrier.unique())
