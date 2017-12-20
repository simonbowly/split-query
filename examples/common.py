
import functools
import os

import appdirs
import six

from split_query.cache import minimal_cache_inmemory, minimal_cache_persistent
from split_query.interface import DataSet


def cache_inmemory():
    def _decorator(cls):
        @functools.wraps(cls)
        def _decorated(*args, **kwargs):
            return minimal_cache_inmemory(cls(*args, **kwargs))
        return _decorated
    return _decorator


def cache_persistent(store_name):
    base_name = 'split-query'
    location = appdirs.user_data_dir(os.path.join(base_name, store_name))
    def _decorator(cls):
        @functools.wraps(cls)
        def _decorated(*args, **kwargs):
            return minimal_cache_persistent(
                cls(*args, **kwargs), location, protocol=2)
        return _decorated
    return _decorator


def dataset(name, attributes):
    def _decorator(cls):
        @functools.wraps(cls)
        def _decorated(*args, **kwargs):
            backend = cls(*args, **kwargs)
            description = cls.__doc__.strip()
            return DataSet(name, attributes, backend, description=description)
        return _decorated
    return _decorator
