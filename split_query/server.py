''' Simple server interface providing a flexible mirror onto a dataset with a
backend cache. The idea is that the original AEMOCauserPays dataset only has
limited remote-side querying. If I want to extract one month's data for one
generator, I have to download the entire national grid data for that month.
The server/mirror functionality means the full dataset can be cached on some
server somewhere (which can download and process the large dataset quickly),
providing an interface which can filter remote-side using other fields. '''

from datetime import datetime
import logging

import msgpack
import numpy as np
import pandas as pd
import zmq

from .core import object_hook, default
from .core.wrappers import ExpressionContainer


def serialise_query(query):
    return msgpack.packb(query, use_bin_type=True, default=default)


def deserialise_query(request):
    return msgpack.unpackb(request, raw=False, object_hook=object_hook)


def serialisable_series(series):
    if series.dtype == np.dtype('<M8[ns]'):
        return series.apply(datetime.timestamp).tolist()
    return series.tolist()


def serialise_dataframe(df):
    serialisable = {
        column: serialisable_series(data)
        for column, data in df.items()
    }
    return msgpack.packb(serialisable, use_bin_type=True)


def deserialise_dataframe(reply):
    return pd.DataFrame(msgpack.unpackb(reply, raw=False))


def serve_zmq(dataset, port):

    context = zmq.Context()
    socket = context.socket(zmq.ROUTER)
    socket.bind(f'tcp://*:{port}')

    logging.info(f'Listening on port {port:d}')

    while True:
        # Decode message and get dataset.
        ident, _, request = socket.recv_multipart()
        query = deserialise_query(request)
        logging.info(f'Received query {query}')
        df = dataset[ExpressionContainer(query)].get()
        # Serialise and return the dataset.
        reply = serialise_dataframe(df)
        socket.send_multipart([ident, b'', reply])
        logging.info('Sent {0:d} rows x {1:d} columns'.format(*df.shape))


def request_zmq(address, query):
        request = serialise_query(query)
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect(address)
        socket.send(request)
        reply = socket.recv()
        return deserialise_dataframe(reply)
