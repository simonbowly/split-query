
import functools
import itertools
from datetime import datetime
import logging
logging.basicConfig(level=logging.INFO)
import urllib

import appdirs
import pandas as pd

from split_query.cache import minimal_cache_persistent
from split_query.core import (And, Attribute, Eq, In, Le, Lt, Ge, Gt,
                              simplify_domain, traverse_expression)
from pedestrians import cache, dataset


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
        df['date'] = pd.to_datetime(df[['Year', 'Month', 'DayofMonth']].rename(
            columns={'DayofMonth': 'Day'}))
        start = datetime(year, month, 1)
        end = (start + pd.tseries.offsets.MonthBegin()).to_pydatetime()
        expression = And([
            Ge(Attribute('date'), start), Lt(Attribute('date'), end)])
        logging.info('Partial: {} -> {}'.format(start, end))
        yield expression, df


def download_tmp(remote_file):
    logging.info('Loading: {}'.format(remote_file))
    file_name, message = urllib.request.urlretrieve(remote_file)
    return file_name


URL_TEMPLATE = 'http://stat-computing.org/dataexpo/2009/{}.csv.bz2'


def get_years(years):
    return map_parts(itertools.chain(*(
        read_by_group(
            download_tmp(URL_TEMPLATE.format(year)),
            grouper=['Year', 'Month'], compression='bz2', chunksize=100000)
        for year in years)))


def _filter_year_only(obj):
    if any(isinstance(obj, cls) for cls in [Eq, In, Le, Lt, Ge, Gt]):
        if obj.attribute == Attribute('date'):
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


def cache_persistent(store_name):
    location = appdirs.user_data_dir(store_name)
    def _decorator(cls):
        @functools.wraps(cls)
        def _decorated(*args, **kwargs):
            return minimal_cache_persistent(cls(*args, **kwargs), location)
        return _decorated
    return _decorator


@dataset(name='How Late Are My Airlines',
         attributes=['date', 'UniqueCarrier'])
@cache_persistent('airline-data')
class AirlineData(object):
    ''' Airlines!! '''

    def get(self, expression):
        ''' Returns the required superset query in parts iterator. '''
        return get_years(expr_to_years(expression))


if __name__ == '__main__':
    arrivals = AirlineData()
    filtered = arrivals[
        arrivals.UniqueCarrier.isin(['US', 'WN']) &
        arrivals.date.between(datetime(1987, 11, 2), datetime(1987, 11, 7))]
    print(filtered.get().shape)
    print(filtered.get().date.min())
    print(filtered.get().date.max())
    print(filtered.get().UniqueCarrier.unique())
