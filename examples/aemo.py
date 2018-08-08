
import io
import logging
import zipfile
from datetime import datetime, timedelta

import pandas as pd
import requests

from split_query.decorators import (
    dataset, cache_persistent, remote_parameters, range_parameter)


logger = logging.getLogger('datasets.aemo')


BASE_URL = 'http://www.nemweb.com.au/Reports/Current/Causer_Pays/'
DATA_FILE_HEADERS = ['datetime', 'element_id', 'variable_id', 'value', 'value_quality']
ELEMENT_NAMES_URL = 'https://www.aemo.com.au/-/media/Files/Electricity/NEM/Data/Ancillary_Services/Elements_FCAS.csv'
ELEMENTS_FILE_HEADERS = ['element_id', 'element_name', 'element_class', 'element_cat']


def read_causer_pays_zip(filepath_or_buffer):
    zip_archive = zipfile.ZipFile(filepath_or_buffer)
    for file_name in zip_archive.filelist:
        df = pd.read_csv(
            io.BytesIO(zip_archive.read(file_name.filename)),
            names=DATA_FILE_HEADERS)
        df['datetime'] = pd.to_datetime(df['datetime'])
        yield df


def load_causer_pays_zipfile(file_name):
    response = requests.get(BASE_URL + file_name)
    return pd.concat(list(read_causer_pays_zip(io.BytesIO(response.content))))


def round_down_30mins(dt):
    return datetime(dt.year, dt.month, dt.day, dt.hour, (dt.minute // 30) * 30)


def offset_30mins(dt):
    return dt + timedelta(minutes=30)


@dataset(name='AEMO Element Names', attributes=ELEMENTS_FILE_HEADERS)
@cache_persistent('aemo_element_names')
class AEMOElementNames(object):
    ''' '''
    def get(self, query):
        ''' Return a dataframe of element names and ids from AEMO site. '''
        assert query is True
        logging.info('Loading AEMO element names.')
        response = requests.get(ELEMENT_NAMES_URL)
        element_names = pd.read_csv(
            io.BytesIO(response.content),
            names=ELEMENTS_FILE_HEADERS)
        element_names['element_name'] = element_names['element_name'].str.strip()
        element_names.head()
        return True, element_names


@dataset(
    name='AEMO Causer Pays',
    attributes=DATA_FILE_HEADERS)
@cache_persistent('aemo_causer_pays')
@remote_parameters(
    range_parameter(
        'datetime', key_lower='from_dt', key_upper='to_dt',
        round_down=round_down_30mins,
        offset=offset_30mins))
class AEMOCauserPays(object):
    ''' '''
    def get(self, from_dt, to_dt):
        assert to_dt.minute in [0, 30]
        assert (to_dt - from_dt) == timedelta(minutes=30)
        file_timestamp = to_dt - timedelta(minutes=5)
        file_name = file_timestamp.strftime('FCAS_%Y%m%d%H%M.zip')
        logger.info(f'Loading {file_name} for {from_dt.isoformat()} -> {to_dt.isoformat()}')
        return load_causer_pays_zipfile(file_name)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    aemo_data = AEMOCauserPays()
    df = aemo_data[aemo_data.datetime.between(datetime(2018, 6, 8, 0, 0), datetime(2018, 6, 8, 2, 1))].get()
    print(df.datetime.min(), df.datetime.max())
