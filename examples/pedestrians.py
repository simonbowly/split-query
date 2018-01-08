
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
from split_query.decorators import cache_inmemory, cache_persistent, dataset


MAP_ID_NAME = {
    1: 'Bourke Street Mall (North)',
    2: 'Bourke Street Mall (South)',
    3: 'Melbourne Central',
    4: 'Town Hall (West)',
    5: 'Princes Bridge',
    6: 'Flinders Street Station Underpass',
    7: 'Birrarung Marr',
    8: 'Webb Bridge',
    9: 'Southern Cross Station',
    10: 'Victoria Point',
    11: 'Waterfront City',
    12: 'New Quay',
    13: 'Flagstaff Station',
    14: 'Sandridge Bridge',
    15: 'State Library',
    16: 'Australia on Collins',
    17: 'Collins Place (South)',
    18: 'Collins Place (North)',
    19: 'Chinatown-Swanston St (North)',
    20: 'Chinatown-Lt Bourke St (South)',
    21: 'Bourke St-Russell St (West)',
    22: 'Flinders St-Elizabeth St (East)',
    23: 'Spencer St-Collins St (South)',
    24: 'Spencer St-Collins St (North)',
    25: 'Melbourne Convention Exhibition Centre',
    26: 'QV Market-Elizabeth St (West)',
    27: 'QV Market-Peel St',
    28: 'The Arts Centre',
    29: 'St Kilda Rd-Alexandra Gardens',
    30: 'Lonsdale St (South)',
    31: 'Lygon St (West)',
    32: 'City Square',
    33: 'Flinders St-Spring St (West)',
    34: 'Flinders St-Spark La',
    35: 'Southbank',
    36: 'Queen St (West)',
    37: 'Lygon St (East)',
    38: 'Flinders St-Swanston St (West)',
    39: 'Alfred Place',
    40: 'Lonsdale St-Spring St (West)',
    42: 'Grattan St-Swanston St (West)',
    43: 'Monash Rd-Swanston St (West)',
    44: 'Tin Alley-Swanston St (West)',
}


MAP_NAME_ID = {value: key for key, value in MAP_ID_NAME.items()}
MAP_ID_NAME = pd.Series(MAP_ID_NAME, name='sensor')


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
    if isinstance(obj, In) and obj.attribute == Attribute('sensor'):
        return Or([Eq(Attribute('sensor_id'), MAP_NAME_ID[name]) for name in obj.valueset])
    return obj


def parse_remote(entry):
    return {
        'datetime': parse_dt(entry['daet_time']),
        'hourly_count': int(entry['qv_market_peel_st']),
        'sensor_id': int(entry['sensor_id'])}


@dataset(
    name='Melbourne Pedestrian Counters',
    attributes=['datetime', 'hourly_count', 'sensor'])
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
        result = result.join(
            MAP_ID_NAME, on='sensor_id').drop(
            columns=['sensor_id'])
        return actual, result


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    pedestrians = PedestrianRemote()
    filtered = pedestrians[
        pedestrians.datetime.between(datetime(2015, 5, 3), datetime(2016, 2, 3)) &
        pedestrians.sensor.isin(['Town Hall (West)', 'Southbank'])]
    print(filtered.get().shape)
    print(filtered.get().datetime.min())
    print(filtered.get().datetime.max())
    print(filtered.get().sensor.unique())
