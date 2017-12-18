
import json
import logging
import os
import shelve
import uuid

import pandas as pd

from .core import (
    And, Not, expand_dnf, simplify_domain, simplify_tree,
    default, object_hook)
from .engine import query_df


def simplify(expression):
    ''' Complete simplification (guarantees reaching False if possible). '''
    try:
        return simplify_tree(simplify_domain(expand_dnf(expression)))
    except:
        logging.warning('Failed simplify: ' + repr(expression))
        raise


class MinimalCache(object):
    ''' Cache implementation that uses cached data as much as possible
    (minimal download policy). Uses a simple iterative algorithm, subtracting
    each cached dataset in sequence from the required data. '''

    def __init__(self, remote):
        self.remote = remote

    def get(self, expression):
        ''' Sequentially eliminates parts of the input query with overlapping
        data from the cache. Queries the remote for any missing entries. '''
        parts = []
        for cached_query, cached_data in self.cache_iter():
            # If the cache element overlaps the current expression, add it
            # to the partial data and replace expression with remainder.
            intersection = simplify(And([expression, cached_query]))
            if intersection is not False:
                parts.append(query_df(cached_data, expression))
                expression = simplify(And([expression, Not(cached_query)]))
            # If there is no remainder, we can stop.
            if expression is False:
                break
        else:
            # No break: there is missing data to be retrieved from remote.
            actual, data = self.remote.get(expression)
            self.cache_add(actual, data)
            parts.append(query_df(data, expression))
        # Assemble final result.
        return pd.concat(parts)


class CachingBackend(MinimalCache):

    def __init__(self, remote):
        super().__init__(remote)
        self._cache = []

    def cache_iter(self):
        return iter(self._cache)

    def cache_add(self, expr, data):
        self._cache.append((expr, data))


class PersistentBackend(MinimalCache):

    def __init__(self, remote, location):
        super().__init__(remote)
        self.location = location
        self.contents_file = os.path.join(self.location, 'contents')

    def cache_iter(self):
        if not os.path.exists(self.location):
            os.makedirs(self.location)
        shelf = shelve.open(self.contents_file)
        for key, data_id in shelf.items():
            expr = json.loads(key, object_hook=object_hook)
            value = pd.read_hdf(os.path.join(self.location, data_id))
            yield expr, value
        shelf.close()

    def cache_add(self, expr, data):
        if not os.path.exists(self.location):
            os.makedirs(self.location)
        shelf = shelve.open(self.contents_file)
        key = json.dumps(expr, default=default)
        data_id = str(uuid.uuid4())
        shelf[key] = data_id
        data.to_hdf(os.path.join(self.location, data_id), key='main', complevel=3)
        shelf.close()


# if cached_query == expression:
#     # Actually an unnecessary special case, but avoids simplification
#     # so will speed things up in some cases.
#     parts.append(cached_data)
#     expression = False
#     break
# BUT it could be further sped up by attempting a lookup of each new
# expression in the cache first (preventing the loop)
# That's a performance guarantee of sorts: if at any stage we reach a query
# which is in the cache in its exact form, there should be no partial construction
# of that component.
