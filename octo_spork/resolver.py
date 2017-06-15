
import collections

from .exceptions import ResolutionError


class Resolver(object):
    '''
    sources: List of objects acting as data sources. In order, each will
        have their :capability method called with a query requirement.
        Required return is (refine, superset, remainder). Source should
        return (None, None, None) if it cannot return anything (e.g. points
        to a different table than that in the query.)
        If the query is resolved each source will be called with the superset
        it returned, so it can return the data.
    engine: Local data engine which processes, filters, joins, unions data
        from sources as necessary.
        :process - Take raw data from a source and put into engine's format.
        :query - Take processed data and apply additional refinement.
        :union - Return the union of several data sets.
    caches: Any time data is retrieved from a source, all caches will have
        this data passed to their :write method along with the query it
        satisfies.
    '''

    def __init__(self, sources, source_tables, engine, caches, cache_tables):
        self.sources = list(sources)
        self.source_tables = [frozenset(tables) for tables in source_tables]
        self.engine = engine
        self.caches = [] if caches is None else list(caches)
        self.cache_tables = [frozenset(tables) for tables in cache_tables]

    def run(self, query):
        datasets = []
        current_query = query

        for cache, tables in zip(self.caches, self.cache_tables):
            if not tables.issuperset(current_query.tables):
                continue
            refine, superset, remainder = cache.capability(current_query)
            if superset is None:
                continue
            datasets.append((cache, superset, refine))
            current_query = remainder
            if remainder is None:
                break

        if current_query is not None:
            # Use remote sources to resolve data outside the cache.
            for source, tables in zip(self.sources, self.source_tables):
                if not tables.issuperset(current_query.tables):
                    continue
                # Decompose query into a function of the available source query.
                refine, superset, remainder = source.capability(current_query)
                if superset is None:
                    # Source cannot provide anything useful, skip it.
                    continue
                # Valid query to be run on the source.
                datasets.append((source, superset, refine))
                # If there is more data to be retrieved, continue to next source.
                current_query = remainder
                if remainder is None:
                    break
            else:
                # No break: there was a remainder after all sources were checked.
                raise ResolutionError('Could not resolve query with the given sources.')

        # Run the stored queries required for resolution, processes, refines
        # and joins using the engine.
        results = []
        for source, superset, refine in datasets:
            data = source.query(superset)
            # Any data not from a cache already can be written to cache.
            if source not in self.caches:
                for cache, tables in zip(self.caches, self.cache_tables):
                    if tables.issuperset(superset.tables):
                        cache.write(superset, data)
            # Transform data to engine's format, refine.
            data = self.engine.process(data)
            if refine is not None:
                data = self.engine.query(data, refine)
            results.append(data)
        if len(results) == 1:
            return results[0]
        else:
            return self.engine.union(*results)
