''' Create and run operation trees to get remote data and run local local
operations in order to resolve a query against a list of sources. '''

import collections

from .exceptions import ResolutionError
from .utils import TypingMixin


class NodeGet(TypingMixin, collections.namedtuple('NodeGet', ['source', 'query'])):
    ''' Indicates the given source should be queried for remote data and
    processed by the engine. '''
    pass


class NodeRefine(TypingMixin, collections.namedtuple('NodeRefine', ['refine', 'child'])):
    ''' Indicates the given 'refine' query should be run on the data generated
    by the child object. '''
    pass


class NodeUnion(TypingMixin, collections.namedtuple('NodeUnion', ['children'])):
    ''' Indicates the data generated by the child objects should be joined
    by row into a combined data set. '''

    def __new__(cls, children):
        return super().__new__(cls, tuple(children))


class DataSources(object):
    ''' Ordered collection of remote sources referencing given tables. '''

    def __init__(self, source_order, source_map, source_tables):
        # FIXME: clunky structure.
        self.source_order = source_order
        self.source_map = source_map
        self.source_tables = source_tables


def create_tree(query, data_sources):
    ''' Recursively checks data sources in priority order to create a
    resolution tree describing how to aggregate remote data. '''

    for _index, source_id in enumerate(data_sources.source_order):

        # FIXME: clunky DataSources structure.
        source_tables = data_sources.source_tables[source_id]
        source = data_sources.source_map[source_id]

        # Skip any source which does not cover all tables in the query.
        if not query.tables.issubset(source_tables):
            continue

        # Ask this source if it can provide relevant data, and how the result
        # would need to be refined/added to.
        source_query, refine, remainder = source.capability(query)
        if source_query is None:
            continue

        # Query to be run on source, add refinement node if necessary.
        if refine is None:
            result = NodeGet(source=source_id, query=source_query)
        else:
            result = NodeRefine(refine=refine, child=NodeGet(
                source=source_id, query=source_query))

        if remainder is None:
            return result
        else:
            # Try to resolve remainder only against sources further down the list.
            sub_sources = DataSources(
                source_order=data_sources.source_order[(_index+1):],
                source_map=data_sources.source_map,
                source_tables=data_sources.source_tables)
            # Union results. If subtree is also a union, its children are
            # promoted upwards to flatten the final tree.
            sub_tree = create_tree(remainder, sub_sources)
            if type(sub_tree) is NodeUnion:
                return NodeUnion(children=[result] + list(sub_tree.children))
            return NodeUnion(children=[result, sub_tree])

    raise ResolutionError('Remaining query part could not be resolved by sources.')


def run_tree(node, data_sources, engine, result_store):
    ''' Recursion on the given resolution tree to create a final result. '''
    if type(node) is NodeGet:
        # Data request terminates traversal (leaf node).
        source = data_sources.source_map[node.source]
        data = source.query(node.query)
        result_store[node.query] = data
        return engine.process(data)
    if type(node) is NodeRefine:
        # Refinement node has a child with processed data.
        return engine.refine(
            data=run_tree(node.child, data_sources, engine, result_store),
            query=node.refine)
    if type(node) is NodeUnion:
        # May have multiple children contributing to the same query.
        return engine.union([
            run_tree(child, data_sources, engine, result_store)
            for child in node.children])
    raise ResolutionError('Resolution tree has an unexpected node type.')