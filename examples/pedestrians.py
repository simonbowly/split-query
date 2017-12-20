
from datetime import datetime
import functools
import logging

import requests
import pandas as pd
from dateutil.parser import parse as parse_dt

from split_query.core import (
    Attribute, Ge, Le, Gt, Lt, And, Or, Eq, In, Not,
    simplify_domain, traverse_expression)
from split_query.remote import to_soql

from common import cache_inmemory, cache_persistent, dataset


class SoQLError(Exception):
    pass


def soda_query(domain, endpoint, **params):
    ''' Formatting of domain, endpoint and parameters. '''
    url = 'https://{0}/resource/{1}.json'.format(domain, endpoint)
    params = {'$' + key: value for key, value in params.items()}
    response = requests.get(url=url, params=params)
    data = response.json()
    if response.status_code == 200:
        return data
    else:
        if 'message' in data:
            raise SoQLError(data['message'])
        elif 'data' in data:
            raise SoQLError('SoQL query error: {query}'.format(**data['data']))
        elif 'code' in data:
            raise SoQLError('SoQL error code: {code}'.format(**data))
        else:
            raise SoQLError('SoQL unknown error: {}'.format(data))


def _widen_to_year(obj):
    if isinstance(obj, Ge) and obj.attribute == Attribute('datetime'):
        return Ge(Attribute('datetime'), datetime(obj.value.year, 1, 1))
    if isinstance(obj, Le) and obj.attribute == Attribute('datetime'):
        return Lt(Attribute('datetime'), datetime(obj.value.year + 1, 1, 1))
    return obj


def _map_soql_where(obj):
    ''' Map a datetime query to numeric year only, convert In to OrEq. '''
    if (isinstance(obj, Ge) or isinstance(obj, Gt)) and obj.attribute == Attribute('datetime'):
        return Ge(Attribute('year'), obj.value.year)
    if (isinstance(obj, Le) or isinstance(obj, Lt)) and obj.attribute == Attribute('datetime'):
        return Le(Attribute('year'), obj.value.year)
    if isinstance(obj, In):
        return Or([Eq(obj.attribute, value) for value in obj.valueset])
    return obj


def parse_remote(entry):
    return {
        'datetime': parse_dt(entry['daet_time']),
        'hourly_count': int(entry['qv_market_peel_st']),
        'sensor_id': int(entry['sensor_id'])}


@dataset(
    name='Melbourne Pedestrian Counters',
    attributes=['datetime', 'hourly_count', 'sensor_id'])
@cache_persistent('pedestrians')
# @cache_inmemory()
class PedestrianRemote(object):
    ''' Hourly pedestrian counts from various intersections in Melbourne. '''

    def __init__(self):
        self.actual_get = functools.partial(soda_query, 'data.melbourne.vic.gov.au', 'cb85-mn2u')
        self.page = 50000

    def paged_get(self, where):
        offset = 0
        while True:
            part = self.actual_get(where=where, limit=self.page, offset=offset)
            for entry in part:
                yield entry
            if len(part) < self.page:
                break
            offset += self.page

    def get(self, expression):
        actual = traverse_expression(expression, hook=_widen_to_year)
        where = to_soql(simplify_domain(traverse_expression(
            expression, hook=_map_soql_where)))
        logging.info('REMOTE: ' + where)
        result = pd.DataFrame(list(map(parse_remote, self.paged_get(where))))
        return actual, result


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    pedestrians = PedestrianRemote()
    filtered = pedestrians[
        pedestrians.datetime.between(datetime(2015, 5, 3), datetime(2016, 2, 3)) &
        pedestrians.sensor_id.isin([27, 28])]
    print(filtered.get().shape)
    print(filtered.get().datetime.min())
    print(filtered.get().datetime.max())
    print(filtered.get().sensor_id.unique())
