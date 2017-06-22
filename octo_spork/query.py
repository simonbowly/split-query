''' Immutable objects to represent data queries. '''

import collections
from datetime import datetime
import math

from .exceptions import DecompositionError
from .utils import TypingMixin


class Column(TypingMixin, collections.namedtuple('Column', ['table', 'name'])):
    pass


class EqualTo(TypingMixin, collections.namedtuple('EqualTo', ['column', 'value'])):

    @property
    def columns(self):
        return frozenset({self.column})


class In(TypingMixin, collections.namedtuple('In', ['column', 'valueset'])):

    def __new__(cls, column, valueset):
        return super().__new__(cls, column, frozenset(valueset))

    @property
    def columns(self):
        return frozenset({self.column})


class Range(TypingMixin, collections.namedtuple('Range', ['column', 'lower', 'upper', 'incl_lower', 'incl_upper', 'lower_inf', 'upper_inf', 'data_type'])):

    def __new__(cls, column, lower, upper, incl_lower, incl_upper, data_type=None):
        if data_type is datetime or type(lower) is datetime or type(upper) is datetime:
            lower_inf = datetime.min
            upper_inf = datetime.max
            data_type = datetime
        else:
            lower_inf = -math.inf
            upper_inf = math.inf
        if lower is None:
            lower = lower_inf
        if upper is None:
            upper = upper_inf
        return super().__new__(cls, column, lower, upper, incl_lower, incl_upper, lower_inf, upper_inf, data_type)

    @property
    def columns(self):
        return frozenset({self.column})


class And(TypingMixin, collections.namedtuple('And', ['expressions'])):

    def __new__(cls, expressions):
        return super().__new__(cls, frozenset(expressions))

    @property
    def columns(self):
        _columns = set()
        for expression in self.expressions:
            _columns.update(expression.columns)
        return frozenset(_columns)

    def simplify(self):
        return (
            next(iter(self.expressions))
            if len(self.expressions) == 1 else self)


class Or(TypingMixin, collections.namedtuple('Or', ['expressions'])):

    def __new__(cls, expressions):
        return super().__new__(cls, frozenset(expressions))

    @property
    def columns(self):
        _columns = set()
        for expression in self.expressions:
            _columns.update(expression.columns)
        return frozenset(_columns)


class Not(TypingMixin, collections.namedtuple('Not', ['expression'])):

    @property
    def columns(self):
        return frozenset({self.expression.column})


def GreaterThan(column, value):
    return Range(column, lower=value, upper=None, incl_lower=False, incl_upper=False)


def GreaterThanOrEqualTo(column, value):
    return Range(column, lower=value, upper=None, incl_lower=True, incl_upper=False)


def LessThan(column, value):
    return Range(column, lower=None, upper=value, incl_lower=False, incl_upper=False)


def LessThanOrEqualTo(column, value):
    return Range(column, lower=None, upper=value, incl_lower=False, incl_upper=True)


def InfiniteRange(column, data_type):
    return Range(column, lower=None, upper=None, incl_lower=False, incl_upper=False, data_type=data_type)


class Query(TypingMixin, collections.namedtuple('Query', ['table', 'select', 'where'])):

    def __new__(cls, table, select=None, where=None):
        # TODO verify components are of correct type and are hashable
        if select is None:
            select = tuple()
        return super().__new__(
            cls, table=table, select=frozenset(select), where=where)

    @property
    def columns(self):
        _columns = set(self.select)
        if self.where is not None:
            _columns.update(self.where.columns)
        return frozenset(_columns)

    @property
    def tables(self):
        _tables = {column.table for column in self.columns}
        _tables.add(self.table)
        return frozenset(_tables)


def decompose(query, source):

    # Query objects: break down into columns and filters.
    if type(query) is Query and type(source) is Query:
        refine, remainder = None, None
        refine_where, remainder_where = decompose(query.where, source.where)
        source_missing = query.select - source.select
        if source_missing:
            raise DecompositionError()
        source_extra = source.select - query.select
        if source_extra:
            refine = Query(table=query.table, select=query.select, where=refine_where)
        if remainder_where is not None:
            remainder = Query(table=query.table, select=query.select, where=remainder_where)
        return refine, remainder

    # Exact match. Nothing to filter out or add.
    if query == source:
        return None, None

    # No filters on source.
    if source is None:  # Need some standing "where anything"?
        return query, None

    # No filters on query.
    if query is None:
        if type(source) is Range:
            return decompose(InfiniteRange(source.column, source.data_type), source)

    # Logical compositions.
    if type(query) is And and type(source) is not And:
        return decompose(query, And([source]))
    if type(query) is not And and type(source) is And:
        return decompose(And([query]), source)
    if type(query) is And and type(source) is And:
        refine, remainder = None, None
        # Missing expressions in source require refinement.
        source_missing = query.expressions - source.expressions
        if source_missing:
            refine = And(source_missing).simplify()
        # Extra expressions in source contribute partials.
        source_extra = source.expressions - query.expressions
        if source_extra:
            remainder = And(query.expressions.union({Not(And(source_extra).simplify())}))
        return refine, remainder

    # Matchable single statements.
    if type(query) is type(source) and query.column == source.column:

        _type = type(query)
        column = query.column

        if _type is In:
            refine, remainder = None, None
            if source.valueset.difference(query.valueset):
                refine = In(column, query.valueset.intersection(source.valueset))
            if query.valueset.difference(source.valueset):
                remainder = In(column, query.valueset.difference(source.valueset))
            return refine, remainder

        if _type is Range:
            refine, remainder = None, None
            # Check if source query needs refining.
            if source.lower < query.lower:
                refine = query
            if source.upper > query.upper:
                refine = query
            # Check if part of the range is missing.
            if source.lower > query.lower:
                remainder = Range(
                    column, lower=query.lower, upper=source.lower,
                    incl_lower=query.incl_lower,
                    incl_upper=not source.incl_lower)
            if source.upper < query.upper:
                _rem = Range(
                    column, lower=source.upper, upper=query.upper,
                    incl_lower=not source.incl_upper,
                    incl_upper=query.incl_upper)
                # In case multiple parts are needed.
                if remainder is None:
                    remainder = _rem
                else:
                    remainder = Or([remainder, _rem])

            return refine, remainder

    raise DecompositionError()
