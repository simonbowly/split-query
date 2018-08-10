''' Dataset object which acts as a client interface to the mirroring server. '''

from datetime import datetime

import pandas as pd
import msgpack
import zmq

from split_query.core import default
from split_query.decorators import dataset
from split_query.server import request_zmq


@dataset(
    name='AEMO Causer Pays Remote',
    attributes=['datetime', 'element_id', 'variable_id', 'value', 'value_quality'])
class AEMOCauserPaysRemote(object):
    ''' No cache needed, just a front end to a local service. '''

    def get(self, query):
        df = request_zmq('tcp://localhost:5566', query)
        # Manual re-typing. Should be captured in the serialisation.
        df.datetime = df.datetime.apply(datetime.fromtimestamp)
        return df


if __name__ == '__main__':
    dataset = AEMOCauserPaysRemote()
    df = dataset[
        dataset.datetime.between(datetime(2018, 7, 1), datetime(2018, 7, 1, 4))
        & dataset.element_id.isin([313, 314])].get()
    print(df.groupby('element_id').datetime.agg(['min', 'max']))
