
import collections
from unittest.mock import Mock, call

import pytest

from octo_spork.resolver import Resolver, ResolutionError
from octo_spork.query import Column, In, Query


# Constants for capability returns.
COL1 = Column('table1', 'column1')
QUERY = Query(table='table1', where=In(COL1, [1, 2, 3, 4]))
SUBSET = Query(table='table1', where=In(COL1, [1, 2]))
REMAINDER = Query(table='table1', where=In(COL1, [3, 4]))
SUPERSET = Query(table='table1', where=In(COL1, [1, 2, 3, 4, 5, 6]))
REFINE = Query(table='table1', where=In(COL1, [1, 2, 3, 4]))


ResolverTestCase = collections.namedtuple('ResolverTestCase', [
    'name',             # Not used, just a label to recognise failed cases.
    'query',            # Passed to resolver.run().
    'sources',          # List of RemoteSpec objects describing source behaviour.
    'caches',           # List of CacheSpec objects describing cache behaviour.
    'engine_calls',     # Expected calls to the engine object.
    'result',           # Expected result of resolver.run().
                        # Expects ResolutionError thrown if this is None.
    ])

RemoteSpec = collections.namedtuple('RemoteSpec', [
    'tables',           # Return value for the tables() method.
    'capability',       # Return value for the capability() method.
    'method_calls',     # All expected calls to corresponding mock.
    ])

CacheSpec = collections.namedtuple('CacheSpec', [
    'tables',           # Return value for the tables() method.
    'capability',       # Return value for the capability() method.
    'method_calls',     # All expected calls to corresponding mock.
    ])


# Single remote source satisfied the requested query exactly.
CASE1 = ResolverTestCase(
    name='single_exact',
    query=QUERY,
    caches=[],
    sources=[
        RemoteSpec(
            tables={'table1'},
            capability=(None, QUERY, None),
            method_calls=[call.capability(QUERY), call.query(QUERY)])],
    engine_calls=[call.process('RQ1')],
    result='EP1')

# Single remote source, empty cache.
CASE1A = ResolverTestCase(
    name='single_exact_empty_cache',
    query=QUERY,
    caches=[
        CacheSpec(
            tables={'table1', 'table2'},
            capability=(None, None, None),
            method_calls=[call.capability(QUERY), call.write(QUERY, 'RQ1')])
    ],
    sources=[
        RemoteSpec(
            tables={'table1', 'table2'},
            capability=(None, QUERY, None),
            method_calls=[call.capability(QUERY), call.query(QUERY)])],
    engine_calls=[call.process('RQ1')],
    result='EP1')

# Cache returns complete dataset. No write calls to cache.
CASE1B = ResolverTestCase(
    name='exact_cache_result',
    query=QUERY,
    caches=[
        CacheSpec(
            tables={'table1'},
            capability=(None, QUERY, None),
            method_calls=[call.capability(QUERY), call.query(QUERY)]),
    ],
    sources=[
        RemoteSpec(
            tables={'table1'}, capability=None, method_calls=[])],
    engine_calls=[call.process('CQ1')],
    result='EP1')

# Partial cache result. Remainder from remote source written to cache.
CASE1C = ResolverTestCase(
    name='cache_remainder',
    query=QUERY,
    caches=[
        CacheSpec(
            tables={'table1'},
            capability=('refine', 'cache_query', REMAINDER),
            method_calls=[
                call.capability(QUERY), call.query('cache_query'),
                call.write(REMAINDER, 'RQ1')]),
    ],
    sources=[
        RemoteSpec(
            tables={'table1'},
            capability=(None, REMAINDER, None),
            method_calls=[call.capability(REMAINDER), call.query(REMAINDER)])],
    engine_calls=[
        call.process('CQ1'), call.query('EP1', 'refine'),
        call.process('RQ1'), call.union('EQ1', 'EP2')],
    result='EU1')

# Single remote source returns a strict superset of the requested result.
CASE2 = ResolverTestCase(
    name='single_superset',
    query=QUERY,
    caches=[],
    sources=[
        RemoteSpec(
            tables={'table1'},
            capability=('refine', 'superset', None),
            method_calls=[call.capability(QUERY), call.query('superset')])],
    engine_calls=[call.process('RQ1'), call.query('EP1', 'refine')],
    result='EQ1')

# First remote returns partial data, remainder comes from second remote.
CASE3 = ResolverTestCase(
    name='subset_remainder',
    query=QUERY,
    caches=[],
    sources=[
        RemoteSpec(
            tables={'table1'},
            capability=('refine1', 'query1', REMAINDER),
            method_calls=[call.capability(QUERY), call.query('query1')]),
        RemoteSpec(
            tables={'table1'},
            capability=('refine2', 'query2', None),
            method_calls=[call.capability(REMAINDER), call.query('query2')])],
    engine_calls=[
        call.process('RQ1'), call.query('EP1', 'refine1'),
        call.process('RQ2'), call.query('EP2', 'refine2'),
        call.union('EQ1', 'EQ2')],
    result='EU1')

# Sources which can't provide relevant data are skipped.
CASE4 = ResolverTestCase(
    name='skip_invalid',
    query=QUERY,
    caches=[],
    sources=[
        RemoteSpec(
            tables={'table1'},
            capability=(None, None, None),
            method_calls=[call.capability(QUERY)]),
        RemoteSpec(
            tables={'table1'},
            capability=(None, QUERY, None),
            method_calls=[call.capability(QUERY), call.query(QUERY)])],
    engine_calls=[call.process('RQ2')],
    result='EP1')

# Some data still required after all sources have been checked (fails).
CASE5 = ResolverTestCase(
    name='fail_single_exhausted',
    query=QUERY,
    caches=[],
    sources=[
        RemoteSpec(
            tables={'table1'},
            capability=(None, None, None),
            method_calls=[call.capability(QUERY)])],
    engine_calls=[],
    result=None)

# Some data still required after all sources have been checked (fails).
CASE6 = ResolverTestCase(
    name='fail_multiple_exhausted',
    query=QUERY,
    caches=[],
    sources=[
        RemoteSpec(
            tables={'table1'},
            capability=(None, 'query1', REMAINDER),
            method_calls=[call.capability(QUERY)]),
        RemoteSpec(
            tables={'table1'},
            capability=(None, None, None),
            method_calls=[call.capability(REMAINDER)])],
    engine_calls=[],
    result=None)

# Only remotes/caches relating to the query tables are used.
CASE7 = ResolverTestCase(
    name='skip_other_tables',
    query=QUERY,
    caches=[
        CacheSpec(
            tables={'table1'},
            capability=(None, None, None),
            method_calls=[call.capability(QUERY), call.write(QUERY, 'RQ2')]),
        CacheSpec(
            tables={'table2'},      # Expect skipped and no write.
            capability=None,
            method_calls=[])
    ],
    sources=[
        RemoteSpec(
            tables={'table2'},      # Expect source to be skipped.
            capability=None,
            method_calls=[]),
        RemoteSpec(
            tables={'table1'},
            capability=(None, QUERY, None),
            method_calls=[call.capability(QUERY), call.query(QUERY)])],
    engine_calls=[call.process('RQ2')],
    result='EP1')


@pytest.mark.parametrize('testcase', [CASE1, CASE1A, CASE1B, CASE1C, CASE2, CASE3, CASE4, CASE5, CASE6, CASE7])
def test_resolver(testcase):
    ''' Queries involving one table, two possible sources. '''

    # Test case specification sets the capability return value.
    remotes = [Mock() for _ in testcase.sources]
    for i, (remote, test_source) in enumerate(zip(remotes, testcase.sources)):
        remote.capability.return_value = test_source.capability
        # 'Dataset' returned will be RQ1, RQ2, ... for successive remotes.
        remote.query.return_value = 'RQ{}'.format(i+1)

    # Cache return values.
    caches = [Mock() for _ in testcase.caches]
    for i, (cache, cache_spec) in enumerate(zip(caches, testcase.caches)):
        cache.capability.return_value = cache_spec.capability
        # Data returned will be CQ1, CQ2, ... for successive caches.
        cache.query.return_value = 'CQ{}'.format(i+1)

    # Preset outputs for engine method calls.
    engine = Mock()
    engine.process.side_effect = ['EP1', 'EP2', 'EP3']
    engine.query.side_effect = ['EQ1', 'EQ2', 'EQ3']
    engine.union.side_effect = ['EU1', 'EU2', 'EU3']

    # Run resolution process, checking for error or correct result.
    resolver = Resolver(
        sources=remotes,
        source_tables=[source.tables for source in testcase.sources],
        engine=engine,
        caches=caches,
        cache_tables=[cache_spec.tables for cache_spec in testcase.caches])
    if testcase.result is None:
        # Test case marked to expect a resolution error.
        with pytest.raises(ResolutionError):
            result = resolver.run(testcase.query)
    else:
        result = resolver.run(testcase.query)
        assert result == testcase.result

    # Remote, cache and engine calls should match specification.
    # Calls are checked regardless of error or return state.
    for remote, test_source in zip(remotes, testcase.sources):
        assert remote.method_calls == test_source.method_calls
    for cache, cache_spec in zip(caches, testcase.caches):
        assert cache.method_calls == cache_spec.method_calls
    assert engine.method_calls == testcase.engine_calls
