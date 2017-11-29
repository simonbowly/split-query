
import itertools
from unittest import mock

import pandas as pd
import pytest

from split_query.cache import CachingBackend
from split_query.core.expressions import And, Or, Not, Le, Lt, Ge, Gt, Attribute
from split_query.engine import query_df
from split_query.core.converters import convert_expression


_data = itertools.product(range(5), repeat=2)
_func = lambda entry: pd.Series(dict(entry, point='{x}:{y}'.format(**entry)))
SOURCE_2D = pd.DataFrame(columns=['x', 'y'], data=list(_data)).apply(_func, axis='columns')
X = Attribute('x')
Y = Attribute('y')


def source_query(expression):
    return query_df(SOURCE_2D, expression)


def assert_results_equal(df1, df2):
    assert sorted(df1.point) == sorted(df2.point)


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
    # Cache should keep all data (no middle layer) and do its own
    # filtering.
    (lambda expr: (True, source_query(True)), [
        (Le(X, 2), Le(X, 2)),
        (Le(X, 3), None),
        ]),
]


@pytest.mark.parametrize('remote_query, sequence', TESTCASES_SEQUENCE)
def test_minimal_download(remote_query, sequence):
    ''' Any cache claiming to minimise the amount of data downloaded should
    satsify these tests for result correctness and remote calls. '''
    remote = mock.Mock()
    if remote_query is None:
        remote.query.side_effect = lambda expr: (expr, source_query(expr))
    else:
        remote.query.side_effect = remote_query
    backend = CachingBackend(remote)
    # Test sequence: run each query to the backend, check that the remote
    # is passed the correct query based on current cache state. Check that
    # the resulting data matches the correct query result. Reset the mock
    # for next loop.
    for orig_expr, remote_expr in sequence:
        result = backend.query(orig_expr)
        if remote_expr is None:
            remote.query.assert_not_called()
        else:
            remote.query.assert_called_once_with(remote_expr)
        assert_results_equal(result, source_query(orig_expr))
        remote.query.reset_mock()


# TODO
# Add a performance test (opportunistic lookups).
