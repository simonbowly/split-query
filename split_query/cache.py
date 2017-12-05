
import logging

import pandas as pd

from .core import And, Not, expand_dnf, simplify_domain, simplify_tree
from .engine import query_df


def simplify(expression):
    ''' Complete simplification (guarantees reaching False if possible). '''
    try:
        return simplify_tree(simplify_domain(expand_dnf(expression)))
    except:
        logging.warning('Failed simplify: ' + repr(expression))
        raise


class CachingBackend(object):
    ''' Cache implementation that uses cached data as much as possible
    (minimal download policy). Uses a simple iterative algorithm, subtracting
    each cached dataset in sequence from the required data. '''

    def __init__(self, remote):
        self.remote = remote
        self.cache = []

    def get(self, expression):
        ''' Sequentially eliminates parts of the input query with overlapping
        data from the cache. Queries the remote for any missing entries. '''
        parts = []
        for cached_query, cached_data in self.cache:
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
            self.cache.append((actual, data))
            parts.append(query_df(data, expression))
        # Assemble final result.
        return pd.concat(parts)


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
