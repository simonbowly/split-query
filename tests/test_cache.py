''' Runs correctness tests on the cache using the pandas query engine. Tests
verify that the result matches the result of running the entire query on the
remote but only requests any new data from the remote.

Equivalent fuzz test could be to run a series of queries, assert that each
result is correct, and assert that each query does not intersect with the
cache contents. But this requires a way to look at the cache contents (may
be implementation specific).

This test is implementation specific too: not all caches must be minimal.
'''

import itertools
import os
import tempfile

import mock
import pandas as pd
import pytest

from split_query.cache import minimal_cache_inmemory, minimal_cache_persistent
from split_query.core.expressions import And, Or, Not, Le, Lt, Ge, Gt, Attribute
from split_query.engine import query_df


# 2D grid source data
_data = itertools.product(range(5), repeat=2)
_func = lambda entry: pd.Series(dict(entry, point='{x}:{y}'.format(**entry)))
SOURCE_2D = pd.DataFrame(columns=['x', 'y'], data=list(_data)).apply(_func, axis='columns')
X = Attribute('x')
Y = Attribute('y')


def source_query(expression):
    ''' Runs a query on the source data using pandas engine. '''
    return query_df(SOURCE_2D, expression)


# Each testcase is a sequence of query pairs: the query passed to the cache,
# and the expected query the cache should run on the remote given the queries
# that have already been run. First element allows the default remote function
# to be overwritten.
TESTCASES_SEQUENCE = [
    # Boring.
    # (None, [
    #     (False, None)]),
    # Independent datasets.
    (None, [
        (Le(X, 2), Le(X, 2)),
        (Ge(X, 3), Ge(X, 3)),
        ]),
    # Exact repetition.
    (None, [
        (Le(X, 3), Le(X, 3)),
        (Le(X, 3), None),
        ]),
    # Following queries are subsets.
    (None, [
        (Le(X, 3), Le(X, 3)),
        (Le(X, 2), None),
        (Le(X, 1), None),
        ]),
    # Following queries overlap partially.
    (None, [
        (Le(X, 1), Le(X, 1)),
        (Le(X, 3), And([Gt(X, 1), Le(X, 3)])),
        ]),
    (None, [
        (Le(X, 2), Le(X, 2)),
        (Ge(X, 1), Gt(X, 2)),
        ]),
    # Multiple cache records stored.
    (None, [
        (Le(X, 1), Le(X, 1)),
        (Ge(X, 3), Ge(X, 3)),
        (Le(X, 0), None),
        (Ge(X, 4), None),
        ]),
    # Assembling a result from partial cached queries.
    (None, [
        (Le(X, 2), Le(X, 2)),
        (True, Gt(X, 2)),
        (True, None),
        ]),
    # Overzealous remote (returns all data).
    # Cache should keep all data (no middle layer) and do its own filtering.
    (lambda expr: (True, source_query(True)), [
        (Le(X, 2), Le(X, 2)),
        (Le(X, 3), None),
        ]),
]


def create_persistent(remote):
    shelf = tempfile.mktemp()
    return minimal_cache_persistent(remote, location=shelf)


@pytest.mark.parametrize('cls', [minimal_cache_inmemory, create_persistent])
@pytest.mark.parametrize('remote_query, sequence', TESTCASES_SEQUENCE)
def test_minimal_download(cls, remote_query, sequence):
    ''' Any cache claiming to minimise the amount of data downloaded should
    satsify these tests for result correctness and remote calls. '''
    remote = mock.Mock()
    if remote_query is None:
        remote.get.side_effect = lambda expr: (expr, source_query(expr))
    else:
        remote.get.side_effect = remote_query
    backend = cls(remote)
    # Test sequence: run each query to the backend, check that the remote
    # is passed the correct query based on current cache state. Check that
    # the resulting data matches the correct query result. Reset the mock
    # for next loop.
    for orig_expr, remote_expr in sequence:
        result = backend.get(orig_expr)
        if remote_expr is None:
            remote.get.assert_not_called()
        else:
            remote.get.assert_called_once_with(remote_expr)
        true_result = source_query(orig_expr)
        assert sorted(result.point) == sorted(true_result.point)
        remote.get.reset_mock()
