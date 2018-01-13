
import logging

import pandas as pd
import numpy as np

from split_query.decorators import (dataset, cache_persistent, remote_parameters,
                                    range_parameter, tag_parameter)


@dataset(name='SampleDataset', attributes=['timestamp', 'tag_name', 'interval', 'value'])
@cache_persistent('sample_data')
@remote_parameters(
    range_parameter('timestamp', key_lower='start_time', key_upper='end_time'),
    tag_parameter('tag_name', single=True),
    tag_parameter('interval', single=True))
class SampleDataset(object):
    ''' This docstring will be displayed in the dataset object repr. '''

    def get(self, start_time, end_time, tag_name, interval):
        ''' Return a dataframe which is the result of querying the remote dataset
        for all records with the given parameters. Since the cache filters based
        on the data, make sure the columns timestamp, tag_name and interval are
        present in the returned dataframes. '''
        logging.info('REMOTE {}[{}]: {} -> {}'.format(
             tag_name, interval, start_time.isoformat(), end_time.isoformat()))
        date_range = pd.date_range(start_time, end_time, freq=interval, name='timestamp')
        df = pd.DataFrame(index=date_range, data=dict(
            tag_name=[tag_name] * date_range.shape[0],
            interval=[interval] * date_range.shape[0],
            value=np.random.random(date_range.shape[0]))).reset_index()
        logging.info('REMOTE {} records'.format(df.shape[0]))
        return df
