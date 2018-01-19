
from datetime import datetime
import logging

import requests
import pandas as pd
from dateutil.parser import parse as parse_dt

from split_query.decorators import dataset, cache_persistent, remote_parameters, range_parameter, tag_parameter


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


def parse_remote(entry):
    return {
        'datetime': parse_dt(entry['daet_time']),
        'hourly_count': int(entry['qv_market_peel_st']),
        'sensor_id': int(entry['sensor_id'])}


def paged_get(domain, endpoint, where, page=5000):
    offset = 0
    while True:
        part = soda_query(domain, endpoint, where=where, limit=page, offset=offset)
        for entry in part:
            yield entry
        if len(part) < page:
            break
        offset += page


@dataset(
    name='Melbourne Pedestrian Counters',
    attributes=['datetime', 'hourly_count', 'sensor'])
@cache_persistent('melb_pedestrians')
@remote_parameters(
    range_parameter(
        'datetime', key_lower='from_dt', key_upper='to_dt',
        round_down=lambda dt: datetime(dt.year, 1, 1, 0, 0, 0),
        offset=lambda dt: datetime(dt.year + 1, 1, 1, 0, 0, 0)),
    tag_parameter('sensor', single=True))
class PedestrianDataset(object):
    ''' This docstring will be displayed in the dataset object repr. '''

    def get(self, from_dt, to_dt, sensor):
        assert from_dt == datetime(from_dt.year, 1, 1, 0, 0, 0)
        assert to_dt == datetime(from_dt.year + 1, 1, 1, 0, 0, 0)
        where = '(sensor_id = {}) and (year = {})'.format(
            MAP_NAME_ID[sensor], from_dt.year)
        logging.info('QUERY: {}'.format(where))
        data = paged_get('data.melbourne.vic.gov.au', 'cb85-mn2u', where)
        result = pd.DataFrame(list(map(parse_remote, data)))
        logging.info('RECORDS: {}'.format(result.shape[0]))
        if result.shape[0] == 0:
            return pd.DataFrame(columns=['datetime', 'hourly_count', 'sensor'], data=[])
        result = result.join(
            MAP_ID_NAME, on='sensor_id').drop(
            columns=['sensor_id'])
        return result


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    pedestrians = PedestrianDataset()
    # pedestrians.clear_cache()
    filtered = pedestrians[
        pedestrians.datetime.between(datetime(2013, 2, 3), datetime(2017, 10, 3)) &
        pedestrians.sensor.isin(['Town Hall (West)', 'Southbank'])]
    print(filtered.get().groupby('sensor').datetime.agg(['min', 'max', 'count']))
