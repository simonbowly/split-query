''' Writing SQL from query objects. '''

import datetime
import math

from .exceptions import SQLRepresentationError
from .query import Column, In, And, Or, Range


def to_sql(obj, alias_map=None):
    ''' Recursive traversal function producing SQL representations of filters. '''

    # Column names and aliases.
    alias_map = dict() if alias_map is None else alias_map
    if type(alias_map) is not dict:
        raise SQLRepresentationError("SQL alias map must be a dictionary.")
    if type(obj) is Column:
        if obj in alias_map:
            return "{0.table}.{0.name} as {1}".format(obj, str(alias_map[obj]))
        return "{0.table}.{0.name}".format(obj)

    # Constant types.
    if type(obj) in [int, float]:
        return str(obj)
    if type(obj) is str:
        return "'{}'".format(obj)
    if type(obj) is datetime.datetime:
        return "'{}'".format(obj.isoformat())

    # Logical expressions.
    if type(obj) is Range:
        expr = []
        if obj.lower > -math.inf:
            expr.append("{} {} {}".format(
                to_sql(obj.column), ">=" if obj.incl_lower else ">",
                to_sql(obj.lower)))
        if obj.upper < math.inf:
            expr.append("{} {} {}".format(
                to_sql(obj.column), "<=" if obj.incl_upper else "<",
                to_sql(obj.upper)))
        return ' and '.join(expr)
    if type(obj) is In:
        return "{} in ({})".format(
            to_sql(obj.column),
            ','.join(to_sql(value) for value in sorted(obj.valueset)))
    if type(obj) is And:
        return ' and '.join(
            "({})".format(to_sql(expression))
            for expression in sorted(obj.expressions))
    if type(obj) is Or:
        return ' or '.join(
            "({})".format(to_sql(expression))
            for expression in sorted(obj.expressions))
    # if type(obj) is Between:
    #     return "{} between {} and {}".format(
    #         to_sql(obj.column), to_sql(obj.lower), to_sql(obj.upper))
    # if type(obj) is Not:
    #     return "not {}".format(to_sql(obj.expression))

    raise SQLRepresentationError("Cannot represent type {} as SQL".format(type(obj)))
