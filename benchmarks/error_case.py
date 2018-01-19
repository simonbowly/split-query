
from datetime import datetime
import logging
logging.basicConfig(level=logging.INFO)

import pandas as pd

from split_query.decorators import dataset, cache_persistent, remote_parameters, range_parameter, tag_parameter


@dataset(
    name='Melbourne Pedestrian Counters',
    attributes=['datetime', 'hourly_count', 'sensor'])
@cache_persistent('error_case')
@remote_parameters(
    range_parameter(
        'datetime', key_lower='from_dt', key_upper='to_dt',
        round_down=lambda dt: datetime(dt.year, 1, 1, 0, 0, 0),
        offset=lambda dt: datetime(dt.year + 1, 1, 1, 0, 0, 0)),
    tag_parameter('sensor', single=True))
class Dataset(object):
    ''' This docstring will be displayed in the dataset object repr. '''

    def get(self, from_dt, to_dt, sensor):
        assert from_dt == datetime(from_dt.year, 1, 1, 0, 0, 0)
        assert to_dt == datetime(from_dt.year + 1, 1, 1, 0, 0, 0)
        where = '(sensor = {}) and (year = {})'.format(sensor, from_dt.year)
        logging.info('QUERY: {}'.format(where))
        return pd.DataFrame(columns=['datetime', 'hourly_count', 'sensor'], data=[])

dataset = Dataset()
dataset.clear_cache()

for start_year in [2016, 2015, 2014, 2013, 2012]:
    logging.info('START {}'.format(start_year))
    logging.info('RESULT\n' + repr(dataset[
        dataset.datetime.between(datetime(start_year, 2, 3), datetime(2017, 10, 3)) &
        dataset.sensor.isin(['Town Hall (West)', 'Southbank'])].get(
        ).groupby('sensor').datetime.agg(['min', 'max', 'count'])))
