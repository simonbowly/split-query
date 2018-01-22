
import functools

import pandas as pd

from .core import And, Eq, Ge, Gt, In, Le, Lt, Not, Or


def map_query_df(df, query):
    ''' Pandas engine implementation applying a query to a dataframe.
    Returns an index on the dataframe. '''
    if isinstance(query, bool):
        return pd.Series(index=df.index, data=query)
    if isinstance(query, Eq):
        return df[query.attribute.name] == query.value
    if isinstance(query, Le):
        return df[query.attribute.name] <= query.value
    if isinstance(query, Ge):
        return df[query.attribute.name] >= query.value
    if isinstance(query, Lt):
        return df[query.attribute.name] < query.value
    if isinstance(query, Gt):
        return df[query.attribute.name] > query.value
    if isinstance(query, In):
        return df[query.attribute.name].isin(query.valueset)
    if isinstance(query, And):
        return functools.reduce(
            lambda ind1, ind2: ind1 & ind2,
            (map_query_df(df, clause) for clause in query.clauses))
    if isinstance(query, Or):
        return functools.reduce(
            lambda ind1, ind2: ind1 | ind2,
            (map_query_df(df, clause) for clause in query.clauses))
    if isinstance(query, Not):
        return ~map_query_df(df, query.clause)
    raise ValueError('Unhandled expression in map_query_df')


def query_df(df, query):
    ''' Use index from map_query_df to return filtered dataframe. '''
    return df[map_query_df(df, query)]
