
class ResolutionError(Exception):
    ''' Thrown when a query could not be resolved against the given sources.
    Used in .resolution_tree module. '''
    pass


class DecompositionError(Exception):
    ''' Thrown when a valid decomposition of the base query in terms of the
    given source query count not be calculated. Used in .query module. '''
    pass


class SQLRepresentationError(Exception):
    ''' Thrown when a valid SQL representation of a query could not be
    created. Used in .sql module. '''
    pass


class EngineError(Exception):
    ''' Thrown when the engine cannot perform the given operation on data. '''
    pass
