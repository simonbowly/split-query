
import functools
import os

import appdirs

from .cache import minimal_cache_inmemory, minimal_cache_persistent
from .interface import DataSet
from .extract import split_parameters


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


def tag_parameter(attr, key=None, single=False):
    key = (key or attr) if single else key + '_values'
    return dict(type='tag', attr=attr, key=key, single=single)


def range_parameter(attr, key_lower=None, key_upper=None, round_down=None, offset=None):
    params = dict(
        type='range', attr=attr,
        key_lower=key_lower or attr + '_lower',
        key_upper=key_upper or attr + '_upper')
    if round_down is not None:
        params.update(round_down=round_down, offset=offset)
    return params


class ParameterWrapper(object):

    def __init__(self, obj, parameters):
        self.obj = obj
        self.parameters = parameters

    def get(self, expression):
        for subquery, kwargs in split_parameters(expression, self.parameters):
            yield subquery, self.obj.get(**kwargs)


def remote_parameters(*parameters):
    def _decorator(cls):
        @functools.wraps(cls)
        def wrapped(*args, **kwargs):
            return ParameterWrapper(cls(*args, **kwargs), parameters)
        return wrapped
    return _decorator
