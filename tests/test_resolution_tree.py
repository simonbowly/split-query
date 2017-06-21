
import collections
import itertools
from unittest.mock import Mock, call

import pytest

from octo_spork.resolution_tree import (
    DataSources, NodeGet, NodeRefine, NodeUnion,
    create_tree, run_tree)
from octo_spork.exceptions import ResolutionError


# Useful common constants.
MockQuery = collections.namedtuple('MockQuery', ['tables', 'name'])

def table1(column_name):
    return MockQuery(frozenset({'table1'}), column_name)

def table2(column_name):
    return MockQuery(frozenset({'table2'}), column_name)

# Test case data containers.
SourceSpec = collections.namedtuple('SourceSpec', [
    'tables', 'capability_values', 'build_calls', 'run_calls'])
ResolverTestCase = collections.namedtuple('ResolverTestCase', [
    'name', 'query', 'sources', 'expected_tree',
    'expected_result', 'engine_calls', 'downloads'])

# First source resolves query to table1 exactly.
CASE_EXACT_T1 = ResolverTestCase(
    name='exact_table1',
    query=table1('main'),
    sources=[
        SourceSpec(
            tables={'table1'},
            capability_values=[(table1('main'), None, None)],
            build_calls=[call.capability(table1('main'))],
            run_calls=[call.query(table1('main'))]),
        SourceSpec(
            tables={'table2'}, capability_values=None,
            build_calls=[], run_calls=[])],
    expected_tree=NodeGet(source=0, query=table1('main')),
    engine_calls=[call.process('RQ0')],
    expected_result='P_RQ0',
    downloads={table1('main'): 'RQ0'})

# Second source resolved query to table2 exactly. First source is associated
# with table1 so it is not considered.
CASE_EXACT_T2 = ResolverTestCase(
    name='exact_table2',
    query=table2('query'),
    sources=[
        SourceSpec(
            tables={'table1'}, capability_values=None,
            build_calls=[], run_calls=[]),
        SourceSpec(
            tables={'table2'},
            capability_values=[(table2('query'), None, None)],
            build_calls=[call.capability(table2('query'))],
            run_calls=[call.query(table2('query'))])],
    expected_tree=NodeGet(source=1, query=table2('query')),
    engine_calls=[call.process('RQ1')],
    expected_result='P_RQ1',
    downloads={table2('query'): 'RQ1'})

# Refinements required.
CASE_REFINE_T1 = ResolverTestCase(
    name='refine_table1',
    query=table1('main'),
    sources=[
        SourceSpec(
            tables={'table1'},
            capability_values=[(table1('src1'), table1('refine1'), None)],
            build_calls=[call.capability(table1('main'))],
            run_calls=[call.query(table1('src1'))])],
    expected_tree=NodeRefine(
        refine=table1('refine1'),
        child=NodeGet(source=0, query=table1('src1'))),
    engine_calls=[
        call.process('RQ0'),
        call.refine(data='P_RQ0', query=table1('refine1'))],
    expected_result='R_P_RQ0',
    downloads={table1('src1'): 'RQ0'})

# Query to second source required to satisfy remainder.
CASE_UNION_T1 = ResolverTestCase(
    name='union_table1',
    query=table1('main'),
    sources=[
        SourceSpec(
            tables={'table1', 'table2'},
            capability_values=[(table1('src1'), None, table1('remainder1'))],
            build_calls=[call.capability(table1('main'))],
            run_calls=[call.query(table1('src1'))]),
        SourceSpec(
            tables={'table1'},
            capability_values=[(table1('remainder1'), None, None)],
            build_calls=[call.capability(table1('remainder1'))],
            run_calls=[call.query(table1('remainder1'))])],
    expected_tree=NodeUnion(children=[
        NodeGet(source=0, query=table1('src1')),
        NodeGet(source=1, query=table1('remainder1'))]),
    engine_calls=[
        call.process('RQ0'), call.process('RQ1'),
        call.union(['P_RQ0', 'P_RQ1'])],
    expected_result='U[P_RQ0,P_RQ1]',
    downloads={table1('src1'): 'RQ0', table1('remainder1'): 'RQ1'})

# Combination of operations.
CASE_COMBINATION_T1 = ResolverTestCase(
    name='union_table1',
    query=table1('main'),
    sources=[
        SourceSpec(
            tables={'table1'},
            capability_values=[
                (table1('src1'), table1('refine1'), table1('remainder1'))],
            build_calls=[call.capability(table1('main'))],
            run_calls=[call.query(table1('src1'))]),
        SourceSpec(
            tables={'table1'},
            capability_values=[(table1('src2'), None, table1('remainder2'))],
            build_calls=[call.capability(table1('remainder1'))],
            run_calls=[call.query(table1('src2'))]),
        SourceSpec(
            tables={'table1'},
            capability_values=[(table1('remainder2'), None, None)],
            build_calls=[call.capability(table1('remainder2'))],
            run_calls=[call.query(table1('remainder2'))])],
    expected_tree=NodeUnion(children=[
        NodeRefine(
            refine=table1('refine1'),
            child=NodeGet(source=0, query=table1('src1'))),
        NodeGet(source=1, query=table1('src2')),
        NodeGet(source=2, query=table1('remainder2'))]),
    engine_calls=[
        call.process('RQ0'),
        call.refine(data='P_RQ0', query=table1('refine1')),
        call.process('RQ1'),
        call.process('RQ2'),
        call.union(['R_P_RQ0', 'P_RQ1', 'P_RQ2'])],
    expected_result='U[R_P_RQ0,P_RQ1,P_RQ2]',
    downloads={
        table1('src1'): 'RQ0', table1('src2'): 'RQ1',
        table1('remainder2'): 'RQ2'})

# Error: run out of data sources.
CASE_ERROR_T1 = ResolverTestCase(
    name='refine_table1',
    query=table1('main'),
    sources=[
        SourceSpec(
            tables={'table1'},
            capability_values=[
                (table1('src1'), table1('refine1'), table1('remainder1'))],
            build_calls=[call.capability(table1('main'))], run_calls=None),
        SourceSpec(
            tables={'table1'},
            capability_values=[(None, None, None)],
            build_calls=[call.capability(table1('remainder1'))], run_calls=None)],
    expected_tree=None,
    engine_calls=None,
    expected_result=None,
    downloads=None)


FULL_WORKING = [
    CASE_EXACT_T1, CASE_EXACT_T2, CASE_REFINE_T1,
    CASE_UNION_T1, CASE_COMBINATION_T1]
TREE_ERROR = [CASE_ERROR_T1]


BUILD_TESTCASES = FULL_WORKING + TREE_ERROR
RUN_TESTCASES = FULL_WORKING


@pytest.mark.parametrize('testcase', BUILD_TESTCASES)
def test_create_tree(testcase):

    # SETUP FOR TREE BUILD
    source_mocks = [Mock() for _ in testcase.sources]
    data_sources = DataSources(
        source_order=[i for i, _ in enumerate(source_mocks)],
        source_map={i: source_mock for i, source_mock in enumerate(source_mocks)},
        source_tables={
            i: source_spec.tables for i, source_spec
            in enumerate(testcase.sources)})

    for source_mock, source_spec in zip(source_mocks, testcase.sources):
        source_mock.capability.side_effect = source_spec.capability_values

    # CHECKS
    if testcase.expected_tree is None:
        with pytest.raises(ResolutionError):
            result = create_tree(testcase.query, data_sources)
    else:
        result = create_tree(testcase.query, data_sources)
        assert result == testcase.expected_tree

    for source_mock, source_spec in zip(source_mocks, testcase.sources):
        assert source_mock.method_calls == source_spec.build_calls


@pytest.fixture(scope='function')
def engine():
    # Nested return keys for engine calls.

    def mock_process(data):
        return 'P_' + data

    def mock_refine(data, query):
        return 'R_' + data

    def mock_union(children):
        return 'U[{}]'.format(','.join(children))
    
    engine = Mock()
    engine.process.side_effect = mock_process
    engine.refine.side_effect = mock_refine
    engine.union.side_effect = mock_union
    return engine


@pytest.mark.parametrize('testcase', RUN_TESTCASES)
def test_run_tree(testcase, engine):

    # SETUP FOR TREE RUN
    source_mocks = [Mock() for _ in testcase.sources]
    data_sources = DataSources(
        source_order=[i for i, _ in enumerate(source_mocks)],
        source_map={i: source_mock for i, source_mock in enumerate(source_mocks)},
        source_tables={
            i: source_spec.tables for i, source_spec
            in enumerate(testcase.sources)})

    for i, (source_mock, source_spec) in enumerate(zip(source_mocks, testcase.sources)):
        source_mock.query.return_value = 'RQ{}'.format(i)

    # CHECKS
    result_store = dict()
    result = run_tree(testcase.expected_tree, data_sources, engine, result_store)
    assert result == testcase.expected_result
    assert result_store == testcase.downloads

    assert engine.method_calls == testcase.engine_calls
    for source_mock, source_spec in zip(source_mocks, testcase.sources):
        assert source_mock.method_calls == source_spec.run_calls
