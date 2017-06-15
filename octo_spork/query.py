
import collections
import datetime

from .exceptions import DecompositionError


class Column(collections.namedtuple('Column', ['table', 'name'])):
    pass


class In(collections.namedtuple('In', ['column', 'valueset'])):

    def __new__(cls, column, valueset):
        return super().__new__(cls, column, frozenset(valueset))

    def decompose(self, other):
        ''' Return refine, remainder for other expression to satisfy this one. '''
        if isinstance(other, self.__class__) and other.column == self.column:
            refine = None
            if other.valueset.difference(self.valueset):
                refine = self.__class__(self.column, self.valueset.intersection(other.valueset))
            remainder = None
            if self.valueset.difference(other.valueset):
                remainder = self.__class__(self.column, self.valueset.difference(other.valueset))
            return refine, remainder
        raise DecompositionError('')

    @property
    def columns(self):
        return frozenset({self.column})

    def inverse(self):
        return Not(self)


class And(collections.namedtuple('And', ['expressions'])):

    def __new__(cls, expressions):
        return super().__new__(cls, frozenset(expressions))

    def decompose(self, other):
        if isinstance(other, self.__class__):
            if self.expressions.difference(other.expressions):
                expr = self.expressions.difference(other.expressions)
                return list(expr)[0] if len(expr) == 1 else And(expr), None
            if self.expressions == other.expressions:
                return None, None
        else:
            # Other is a single expression, wrap it in And so it is comparable.
            return self.decompose(self.__class__({other}))
        raise DecompositionError('')

    @property
    def columns(self):
        _columns = set()
        for expression in self.expressions:
            _columns.update(expression.columns)
        return frozenset(_columns)


class Or(collections.namedtuple('Or', ['expressions'])):

    def __new__(cls, expressions):
        return super().__new__(cls, frozenset(expressions))

    def decompose(self, other):
        if isinstance(other, self.__class__):
            if self.expressions.difference(other.expressions):
                expr = self.expressions.difference(other.expressions)
                return None, list(expr)[0] if len(expr) == 1 else And(expr)
            if self.expressions == other.expressions:
                return None, None
        else:
            # Other is a single expression, wrap it in And so it is comparable.
            return self.decompose(self.__class__({other}))
        raise DecompositionError('')

    @property
    def columns(self):
        _columns = set()
        for expression in self.expressions:
            _columns.update(expression.columns)
        return frozenset(_columns)


class Between(collections.namedtuple('Between', ['column', 'lower', 'upper'])):

    def decompose(self, other):
        if isinstance(other, self.__class__):
            if other.column == self.column:
                refine, remainder = None, None
                if other.lower < self.lower or other.upper > self.upper:
                    # Something in the result still needs to be filtered out.
                    refine = self
                if other.lower > self.lower:
                    remainder = Between(self.column, self.lower, other.lower)
                if other.upper < self.upper:
                    upper_remainder = Between(self.column, other.upper, self.upper)
                    if remainder is None:
                        remainder = upper_remainder
                    else:
                        remainder = Or([remainder, upper_remainder])
                return refine, remainder
        raise DecompositionError('')

    @property
    def columns(self):
        return frozenset({self.column})


class Not(collections.namedtuple('Not', ['expression'])):
    pass


class GE(collections.namedtuple('GE', ['column', 'value'])):

    __symbol__ = '>='

    def inverse(self):
        return LT(self.column, self.value)


class GT(collections.namedtuple('GT', ['column', 'value'])):

    __symbol__ = '>'

    def inverse(self):
        return LT(self.column, self.value)


class LE(collections.namedtuple('LE', ['column', 'value'])):

    __symbol__ = '<='

    def inverse(self):
        return LT(self.column, self.value)


class LT(collections.namedtuple('LT', ['column', 'value'])):

    __symbol__ = '<'

    def inverse(self):
        return LT(self.column, self.value)


def decompose_where(where_main, where_other):
    if where_main is None:
        return None, where_other.inverse()
    if where_other is None:
        return where_main, None
    return where_main.decompose(where_other)


def decompose_select(select_main, select_other):
    ''' Assumes set data structures as stored by Query. '''
    if select_main == select_other:
        return None
    if select_main.issubset(select_other):
        return select_main
    raise DecompositionError('')


Join = collections.namedtuple('Join', ['main', 'joined', 'kind'])


class Query(collections.namedtuple('Query', ['table', 'select', 'where'])):

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
