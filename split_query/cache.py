
from builtins import super

from contextlib import closing
import json
import logging
import os
import shelve
import uuid

import pandas as pd

from .core import (And, Not, expand_dnf, simplify_domain, simplify_tree,
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
    each cached dataset in sequence from the required data. The :cache object
    must implement the dictionary interface (getitem/setitem/keys). '''

    def __init__(self, remote, cache):
        self.remote = remote
        self.cache = cache

    def get(self, expression):
        ''' Sequentially eliminates parts of the input query with overlapping
        data from the cache. Queries the remote for any missing entries. '''
        plan = []
        for cached_query in self.cache.keys():
            # If the cache element overlaps the current expression, add it
            # to the partial data and replace expression with remainder.
            intersection = simplify(And([expression, cached_query]))
            if intersection is not False:
                plan.append((cached_query, expression))
                expression = simplify(And([expression, Not(cached_query)]))
            # If there is no remainder, we can stop.
            if expression is False:
                break
        else:
            # No break: there is missing data to be retrieved from remote.
            actual, data = self.remote.get(expression)
            self.cache[actual] = data
            plan.append((actual, expression))
            expression = simplify(And([expression, Not(actual)]))
            assert expression is False          # TODO query not satisfied.
        # Assemble result from the plan.
        return pd.concat(
            query_df(self.cache[cached_query], filter_query)
            for cached_query, filter_query in plan)


class PersistentDict(object):
    ''' dict-like interface which keeps a contents file using shelve and
    writes data using hdf5. Expression keys are serialised to JSON (shelf data
    must be binary-encodable).
    TODO keep an in-memory copy of contents for faster __getitem__. '''

    def __init__(self, location):
        self.location = location
        self.contents_file = os.path.join(self.location, 'contents')
        self.local_contents = dict()

    @staticmethod
    def decode_shelf(shelf):
        return {
            json.loads(key, object_hook=object_hook): data_id
            for key, data_id in shelf.items()}

    def _update_local_contents(self):
        ''' Reads the contents file to update the local copy. Expression keys
        are decoded. '''
        if not os.path.exists(self.location):
            os.makedirs(self.location)
        with closing(shelve.open(self.contents_file)) as shelf:
            self.local_contents = self.decode_shelf(shelf)

    def keys(self):
        ''' Update local_contents and return expression keys. '''
        self._update_local_contents()
        return self.local_contents.keys()

    def __getitem__(self, expression):
        ''' Return data corresponding to the given :expression. If :expression
        is not in the local copy of contents, update local copy before
        attempting to get the data identifier. '''
        if expression not in self.local_contents:
            self._update_local_contents()
        data_id = self.local_contents[expression]
        return pd.read_hdf(os.path.join(self.location, data_id))

    def __setitem__(self, expression, data):
        ''' Write a new expression key to contents shelf with a unique data
        identifier, write data to file given by the identifier. Updates
        local_contents after adding the new key. Data is written first, so if
        there are errors in data writing, the contents will not be updated. '''
        data_id = str(uuid.uuid4())
        data.to_hdf(os.path.join(self.location, data_id), key='main', complevel=3)
        if not os.path.exists(self.location):
            os.makedirs(self.location)
        with closing(shelve.open(self.contents_file)) as shelf:
            key = json.dumps(expression, default=default)
            shelf[key] = data_id
            self.local_contents = self.decode_shelf(shelf)


def minimal_cache_inmemory(remote):
    return MinimalCache(remote, dict())


def minimal_cache_persistent(remote, location):
    return MinimalCache(remote, PersistentDict(location))


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
