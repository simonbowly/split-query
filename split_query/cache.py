
from builtins import super
from contextlib import closing
import collections
import json
import logging
import os
import shelve
import uuid

import pandas as pd

from .core import And, Or, Not, to_dnf_simplified, default, object_hook
from .engine import query_df


def simplify(expression):
    ''' Speeds up cache return for repeated calls. '''
    result = to_dnf_simplified(expression)
    if type(result) is Or and len(result.clauses) == 1:
        return result.clauses[0]
    return result


class MinimalCache(object):
    ''' Cache implementation that uses cached data as much as possible
    (minimal download policy). Uses a simple iterative algorithm, subtracting
    each cached dataset in sequence from the required data. The :cache object
    must implement the dictionary interface (getitem/setitem/keys). '''

    def __init__(self, remote, cache):
        self.remote = remote
        self.cache = cache
        # Tracks most recent execution path.
        self.tracking = []

    def get(self, expression):
        ''' Sequentially eliminates parts of the input query with overlapping
        data from the cache. Queries the remote for any missing entries. '''
        plan = []
        tracking = []
        for cached_query in self.cache.keys():
            # If the cache element overlaps the current expression, add it
            # to the partial data and replace expression with remainder.
            tracking.append(('cache', expression, cached_query))
            intersection = simplify(And([expression, cached_query]))
            if intersection is not False:
                plan.append((cached_query, expression))
                expression = simplify(And([expression, Not(cached_query)]))
            # If there is no remainder, we can stop.
            if expression is False:
                break
        else:
            # No break: there is missing data to be retrieved from remote.
            remote_result = self.remote.get(expression)
            # Response should be a single (query, data) tuple of an iterable
            # of the entries matching that spec.
            if isinstance(remote_result, tuple):
                assert len(remote_result) == 2
                remote_result = [remote_result]
            # Continues the query planning process as above, while writing
            # new data to the cache.
            for remote_query, remote_data in remote_result:
                # Input new data, add to the plan if useful.
                assert remote_query not in self.cache.keys()
                self.cache[remote_query] = remote_data
                tracking.append(('remote', expression, remote_query))
                intersection = simplify(And([expression, remote_query]))
                if intersection is not False:
                    plan.append((remote_query, expression))
                    expression = simplify(And([expression, Not(remote_query)]))
            # Don't break when complete (this would skip caching some remote
            # data), but verify completeness after loop.
            assert expression is False, expression
        # Assemble result from the plan.
        self.tracking = tracking
        return pd.concat(
            query_df(self.cache[cached_query], filter_query)
            for cached_query, filter_query in plan)

    def clear_cache(self):
        if hasattr(self.cache, 'clear_cache'):
            self.cache.clear_cache()


class PersistentDict(object):
    ''' dict-like interface which keeps a contents file using shelve and
    writes data using hdf5. Expression keys are serialised to JSON (shelf data
    must be binary-encodable). Implementation assumes only one PersistentDict
    is accessing the store at a time (loads shelf on start then updates the
    local copy only when modifying). '''

    def __init__(self, location, protocol=None):
        self.location = location
        self.contents_file = os.path.join(self.location, 'contents')
        self.protocol = protocol
        if not os.path.exists(self.location):
            os.makedirs(self.location)
        with closing(shelve.open(self.contents_file, protocol=self.protocol)) as shelf:
            self.local_contents = self.decode_shelf(shelf)

    @staticmethod
    def decode_shelf(shelf):
        return {
            json.loads(key, object_hook=object_hook): data_id
            for key, data_id in shelf.items()}

    def keys(self):
        ''' Update local_contents and return expression keys. '''
        return self.local_contents.keys()

    def __getitem__(self, expression):
        ''' Return data corresponding to the given :expression. If :expression
        is not in the local copy of contents, update local copy before
        attempting to get the data identifier. '''
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
        with closing(shelve.open(self.contents_file, protocol=self.protocol)) as shelf:
            key = json.dumps(expression, default=default)
            shelf[key] = data_id
            self.local_contents = self.decode_shelf(shelf)

    def clear_cache(self):
        for data_id in self.local_contents.values():
            data_file = os.path.join(self.location, data_id)
            if os.path.exists(data_file):
                os.remove(data_file)
        if os.path.exists(self.contents_file):
            os.remove(self.contents_file)
        self.local_contents = dict()


def minimal_cache_inmemory(remote):
    return MinimalCache(remote, dict())


def minimal_cache_persistent(remote, location, **kwargs):
    return MinimalCache(remote, PersistentDict(location, **kwargs))


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

# Is there a use case for terminating iterative remote reads early so the remote
# can be very dumb and simply iterate over the component parts of the dataset?
# That would be a different kind of cache...
