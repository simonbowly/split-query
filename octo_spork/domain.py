
import functools

import sympy as sp

from .expressions import Attribute, Eq, Le, Lt, Ge, Gt, In, And, Or, Not


def to_interval(expression):
    if isinstance(expression, Le):
        return sp.Interval(-sp.S.Infinity, expression.value)
    if isinstance(expression, Lt):
        return sp.Interval.open(-sp.S.Infinity, expression.value)
    if isinstance(expression, Ge):
        return sp.Interval(expression.value, sp.S.Infinity)
    if isinstance(expression, Gt):
        return sp.Interval.open(expression.value, sp.S.Infinity)
    if isinstance(expression, Not):
        return to_interval(expression.clause).complement(sp.S.Reals)
    if isinstance(expression, And):
        return functools.reduce(
            lambda x, y: x.intersection(y),
            map(to_interval, expression.clauses))
    if isinstance(expression, Or):
        return functools.reduce(
            lambda x, y: x.union(y),
            map(to_interval, expression.clauses))
    raise ValueError('Unhandled expression in _to_interval')


def from_interval(column, interval):
    if isinstance(interval, sp.Union):
        return Or(from_interval(column, arg) for arg in interval.args)
    if isinstance(interval, sp.EmptySet):
        return False
    if interval.left == -sp.S.Infinity:
        if interval.right == sp.S.Infinity:
            return True
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


def to_set(expression):
    if isinstance(expression, In):
        return (expression.valueset, '+')
    if isinstance(expression, And):
        return functools.reduce(
            _reduce_set_and, map(to_set, expression.clauses))
    if isinstance(expression, Or):
        return functools.reduce(
            _reduce_set_or, map(to_set, expression.clauses))
    if isinstance(expression, Not):
        if isinstance(expression.clause, In):
            return (expression.clause.valueset, '-')
    raise ValueError('Unhandled expression in _to_set')


def from_set(column, _set):
    values, sgn = _set
    if sgn == '+':
        return In(column, values)
    else:
        return Not(In(column, values))


def get_attributes(expr):
    if isinstance(expr, Attribute):
        return {expr}
    if any(isinstance(expr, t) for t in [And, Or]):
        return functools.reduce(
            lambda a, b: a.union(b),
            map(get_attributes, expr.clauses))
    if isinstance(expr, Not):
        return get_attributes(expr.clause)
    if any(isinstance(expr, t) for t in [Eq, Le, Lt, Ge, Gt, In]):
        return get_attributes(expr.attribute)
    raise ValueError()


def simplify_sets(expression):
    ''' Simplify a set expression on a single attribute. '''
    attributes = get_attributes(expression)
    if len(attributes) != 1:
        raise ValueError()
    attribute = next(iter(attributes))
    return from_set(attribute, to_set(expression))


def simplify_intervals(expression):
    ''' Simplify an interval expression on a single attribute. '''
    attributes = get_attributes(expression)
    if len(attributes) != 1:
        raise ValueError()
    attribute = next(iter(attributes))
    return from_interval(attribute, to_interval(expression))
