
import collections
import functools

import sympy as sp

from .utils import TypingMixin


class Le(TypingMixin, collections.namedtuple('Le', ['column', 'value'])):
    pass


class Lt(TypingMixin, collections.namedtuple('Lt', ['column', 'value'])):
    pass


class Ge(TypingMixin, collections.namedtuple('Ge', ['column', 'value'])):
    pass


class Gt(TypingMixin, collections.namedtuple('Gt', ['column', 'value'])):
    pass


class And(TypingMixin, collections.namedtuple('And', ['expressions'])):

    def __new__(cls, expressions):
        return super().__new__(cls, frozenset(expressions))


class Or(TypingMixin, collections.namedtuple('Or', ['expressions'])):

    def __new__(cls, expressions):
        return super().__new__(cls, frozenset(expressions))


class Not(TypingMixin, collections.namedtuple('Not', ['expression'])):
    pass


class In(TypingMixin, collections.namedtuple('In', ['column', 'valueset'])):

    def __new__(cls, column, valueset):
        return super().__new__(cls, column, frozenset(valueset))


def _to_interval(expression):
    if type(expression) is Le:
        return sp.Interval(-sp.S.Infinity, expression.value)
    if type(expression) is Lt:
        return sp.Interval.open(-sp.S.Infinity, expression.value)
    if type(expression) is Ge:
        return sp.Interval(expression.value, sp.S.Infinity)
    if type(expression) is Gt:
        return sp.Interval.open(expression.value, sp.S.Infinity)
    if type(expression) is Not:
        return _to_interval(expression.expression).complement(sp.S.Reals)
    if type(expression) is And:
        return functools.reduce(
            lambda x, y: x.intersection(y),
            (_to_interval(expr) for expr in expression.expressions))
    if type(expression) is Or:
        return functools.reduce(
            lambda x, y: x.union(y),
            (_to_interval(expr) for expr in expression.expressions))


def _from_interval(column, interval):
    if type(interval) is sp.Union:
        return Or(_from_interval(column, arg) for arg in interval.args)
    if interval.left == -sp.S.Infinity:
        if interval.right_open:
            return Lt(column, interval.right)
        else:
            return Le(column, interval.right)
    elif interval.right == sp.S.Infinity:
        if interval.left_open:
            return Gt(column, interval.left)
        else:
            return Ge(column, interval.left)
    return And([
        Gt(column, interval.left) if interval.left_open else Ge(column, interval.left),
        Lt(column, interval.right) if interval.right_open else Le(column, interval.right)])


def _reduce_set_and(expr1, expr2):
    values1, sgn1 = expr1
    values2, sgn2 = expr2
    if sgn1 == '+' and sgn2 == '+':
        return values1.intersection(values2), '+'
    if sgn1 == '-' and sgn2 == '-':
        raise ValueError('Invalid set reduction And(Not In, Not In)')
    parts = (values1, values2) if sgn1 == '+' else (values2, values1)
    return (parts[0] - parts[1]), '+'


def _reduce_set_or(expr1, expr2):
    values1, sgn1 = expr1
    values2, sgn2 = expr2
    if sgn1 == '+' and sgn2 == '+':
        return values1.union(values2), '+'
    raise ValueError('Invalid set reduction Or(~In, ~In)')


def _to_set(expression):
    if type(expression) is In:
        return (expression.valueset, '+')
    if type(expression) is And:
        return functools.reduce(
            _reduce_set_and,
            (_to_set(expr) for expr in expression.expressions))
    if type(expression) is Or:
        return functools.reduce(
            _reduce_set_or,
            (_to_set(expr) for expr in expression.expressions))
    if type(expression) is Not:
        return (expression.expression.valueset, '-')


def _from_set(column, _set):
    values, sgn = _set
    if sgn == '+':
        return In(column, values)
    else:
        return Not(In(column, values))
