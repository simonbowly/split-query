
import collections
import functools


class TypingMixin(object):
    ''' Mixin for classes based on namedtuples. Name of class is included
    in hashing and comparisons so that two different object types represented
    by the same tuple are considered to be unequal. '''

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return super().__eq__(other)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.__class__.__name__, super().__hash__()))


def typedtuple(name, fields):
    class TheClass(TypingMixin, collections.namedtuple(name, fields)):
        pass
    TheClass.__name__ = name
    return TheClass


class Column(typedtuple('Column', ['table', 'name'])):
    pass


class Le(typedtuple('Le', ['column', 'value'])):
    pass


class Lt(typedtuple('Lt', ['column', 'value'])):
    pass


class Ge(typedtuple('Ge', ['column', 'value'])):
    pass


class Gt(typedtuple('Gt', ['column', 'value'])):
    pass


class In(typedtuple('In', ['column', 'valueset'])):

    def __new__(cls, column, valueset):
        return super().__new__(cls, column, frozenset(valueset))


class And(typedtuple('And', ['expressions'])):

    def __new__(cls, expressions):
        return super().__new__(cls, frozenset(expressions))


class Or(typedtuple('Or', ['expressions'])):

    def __new__(cls, expressions):
        return super().__new__(cls, frozenset(expressions))


class Not(typedtuple('Not', ['expression'])):
    pass


def get_categories(expression):
    if any(isinstance(expression, t) for t in [Gt, Ge, Lt, Le]):
        return frozenset({(expression.column, 'interval')})
    if isinstance(expression, In):
        return frozenset({(expression.column, 'set')})
    if isinstance(expression, Not):
        return get_categories(expression.expression)
    if isinstance(expression, And) or isinstance(expression, Or):
        return frozenset(functools.reduce(
            lambda c1, c2: c1.union(c2),
            (get_categories(expr) for expr in expression.expressions)))
    raise ValueError('Unknown expression type.')


def get_columns(expression):
    return frozenset(column for column, _ in get_categories(expression))


def get_kinds(expression):
    return frozenset(kind for _, kind in get_categories(expression))
