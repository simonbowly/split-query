
from datetime import datetime, timezone
import functools
import logging
import os
import urllib.request

import pandas as pd

from split_query.core import *
from split_query.cache import PersistentBackend
from pedestrians import dataset, cache


def cache(location):
    def _decorator(cls):
        @functools.wraps(cls)
        def _decorated(*args, **kwargs):
            return PersistentBackend(cls(*args, **kwargs), location=location)
        return _decorated
    return _decorator


def _filter_year_only(obj):
    if any(isinstance(obj, cls) for cls in [Eq, In, Le, Lt, Ge, Gt]):
        if obj.attribute == Attribute('date'):
            if isinstance(obj, Gt) or isinstance(obj, Ge):
                return Ge(Attribute('date'), datetime(obj.value.year, 1, 1))
            if isinstance(obj, Lt) or isinstance(obj, Le):
                return Lt(Attribute('date'), datetime(obj.value.year + 1, 1, 1))
            return obj
        else:
            return True
    return obj


def _map_datetime_year(obj):
    if isinstance(obj, Ge) and obj.attribute == Attribute('date'):
        return Ge(Attribute('year'), obj.value.year)
    if isinstance(obj, Lt) and obj.attribute == Attribute('date'):
        return Le(Attribute('year'), obj.value.year - 1)
    return obj


URL_TEMPLATE = 'http://stat-computing.org/dataexpo/2009/{}.csv.bz2'


@dataset(name='How Late Are My Airlines',
         attributes=['date', 'UniqueCarrier'])
@cache(os.path.join(os.environ['HOME'], '.split-query', 'airlines'))
class AirlineData(object):
    ''' Airlines!! '''

    def load_year(self, year):
        remote_file = URL_TEMPLATE.format(year)
        logging.info('Loading: {}'.format(remote_file))
        file_name, message = urllib.request.urlretrieve(remote_file)
        data = pd.read_csv(file_name, compression='bz2')
        return data

    def get(self, expression):
        actual = simplify_tree(traverse_expression(expression, hook=_filter_year_only))
        year_expr = traverse_expression(actual, hook=_map_datetime_year)
        _intersections = (
            simplify_domain(And([year_expr, Eq(Attribute('year'), year)]))
            for year in range(1987, 2009))
        years = [int(obj.value) for obj in _intersections if obj is not False]
        # Let get() return a list of partial results...
        result = pd.concat(self.load_year(year) for year in years)
        result['date'] = pd.to_datetime(result[['Year', 'Month', 'DayofMonth']].rename(
            columns={'DayofMonth': 'Day'}))
        return actual, result


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)
    dataset = AirlineData()
    print(dataset[dataset.UniqueCarrier.isin(['US', 'WN']) & dataset.date.between(
        datetime(1988, 11, 1, tzinfo=timezone.utc),
        datetime(1988, 12, 1, tzinfo=timezone.utc))].get().date.describe())
