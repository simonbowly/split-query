
import math

import pandas as pd

from .query import EqualTo, In, Range, And
from .exceptions import EngineError


class PandasEngine(object):

    def process(self, data):
        return pd.DataFrame(data)

    def _refine_where(self, data, where):
        if type(where) is EqualTo:
            return data[data[where.column.name] == where.value]
        if type(where) is In:
            return data[data[where.column.name].isin(where.valueset)]
        if type(where) is Range:
            if where.lower > where.lower_inf:
                data = data[data[where.column.name] > where.lower]
            if where.upper < where.upper_inf:
                data = data[data[where.column.name] < where.upper]
            return data
        if type(where) is And:
            for expression in where.expressions:
                data = self._refine_where(data, expression)
            return data
        raise EngineError()

    def refine(self, data, query):
        if query.where is not None:
            data = self._refine_where(data, query.where).reset_index(drop=True)
        return data[[col.name for col in query.select]]

    def union(self, parts):
        return pd.concat(parts).reset_index(drop=True)
