
import functools

import sympy as sp

from .functions import Le, Lt, Ge, Gt, In, And, Or, Not, get_categories


def simplify_sets(expression):
    ''' Simplify a set expression on a single column. '''
    categories = get_categories(expression)
    if len(categories) != 1:
        raise ValueError()
    column, kind = next(iter(categories))
    if kind != 'set':
        raise ValueError()
    return _from_set(column, _to_set(expression))


def simplify_intervals(expression):
    ''' Simplify an interval expression on a single column. '''
    categories = get_categories(expression)
    if len(categories) != 1:
        raise ValueError()
    column, kind = next(iter(categories))
    if kind != 'interval':
        raise ValueError()
    return _from_interval(column, _to_interval(expression))


def _to_interval(expression):
    if isinstance(expression, Le):
        return sp.Interval(-sp.S.Infinity, expression.value)
    if isinstance(expression, Lt):
        return sp.Interval.open(-sp.S.Infinity, expression.value)
    if isinstance(expression, Ge):
        return sp.Interval(expression.value, sp.S.Infinity)
    if isinstance(expression, Gt):
        return sp.Interval.open(expression.value, sp.S.Infinity)
    if isinstance(expression, Not):
        return _to_interval(expression.expression).complement(sp.S.Reals)
    if isinstance(expression, And):
        return functools.reduce(
            lambda x, y: x.intersection(y),
            (_to_interval(expr) for expr in expression.expressions))
    if isinstance(expression, Or):
        return functools.reduce(
            lambda x, y: x.union(y),
            (_to_interval(expr) for expr in expression.expressions))
    raise ValueError('Unhandled expression in _to_interval')


def _from_interval(column, interval):
    if isinstance(interval, sp.Union):
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
    if isinstance(expression, In):
        return (expression.valueset, '+')
    if isinstance(expression, And):
        return functools.reduce(
            _reduce_set_and,
            (_to_set(expr) for expr in expression.expressions))
    if isinstance(expression, Or):
        return functools.reduce(
            _reduce_set_or,
            (_to_set(expr) for expr in expression.expressions))
    if isinstance(expression, Not):
        return (expression.expression.valueset, '-')
    raise ValueError('Unhandled expression in _to_set')


def _from_set(column, _set):
    values, sgn = _set
    if sgn == '+':
        return In(column, values)
    else:
        return Not(In(column, values))
