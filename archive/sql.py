''' Writing SQL from query objects. '''

import datetime
import math

from .exceptions import SQLRepresentationError
from .query import Column, In, And, Or, Range, EqualTo, Not, Query


class SQLRepresentor(object):

    def __init__(self, sources=None):
        if sources is None:
            sources = dict()
        self.sources = sources

    def repr(self, obj):
        ''' Recursive traversal function producing SQL representations of filters. '''

        # Column names and aliases.
        if type(obj) is Column:
            if obj in self.sources:
                return self.sources[obj]
            return "{0.table}.{0.name}".format(obj)

        # Constant types.
        if type(obj) in [int, float]:
            return str(obj)
        if type(obj) is str:
            return "'{}'".format(obj)
        if type(obj) is datetime.datetime:
            return "'{}'".format(obj.isoformat())

        # Logical expressions.
        if type(obj) is EqualTo:
            return "{} = {}".format(self.repr(obj.column), self.repr(obj.value))
        if type(obj) is Range:
            expr = []
            if obj.lower > obj.lower_inf:
                expr.append("{} {} {}".format(
                    self.repr(obj.column), ">=" if obj.incl_lower else ">",
                    self.repr(obj.lower)))
            if obj.upper < obj.upper_inf:
                expr.append("{} {} {}".format(
                    self.repr(obj.column), "<=" if obj.incl_upper else "<",
                    self.repr(obj.upper)))
            return ' and '.join(expr)
        if type(obj) is In:
            return "{} in ({})".format(
                self.repr(obj.column),
                ','.join(self.repr(value) for value in sorted(obj.valueset)))
        if type(obj) is And:
            return ' and '.join(
                "({})".format(self.repr(expression))
                for expression in sorted(obj.expressions))
        if type(obj) is Or:
            return ' or '.join(
                "({})".format(self.repr(expression))
                for expression in sorted(obj.expressions))

        if type(obj) is Not:
            return "not {}".format(self.repr(obj.expression))

        # if type(obj) is Between:
        #     return "{} between {} and {}".format(
        #         self.repr(obj.column), self.repr(obj.lower), self.repr(obj.upper))

        if type(obj) is Query:
            return "select {} where {}".format(
                ', '.join(sorted(self.repr(col) for col in obj.select)),
                self.repr(obj.where))

        raise SQLRepresentationError("Cannot represent type {} as SQL".format(type(obj)))
