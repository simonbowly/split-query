
import collections
import functools
import itertools

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


def flatten(expression):
    if isinstance(expression, And) or isinstance(expression, Or):
        if len(expression.expressions) == 1:
            return next(iter(expression.expressions))
        cls = expression.__class__
        exprs = map(flatten, expression.expressions)
        return cls(itertools.chain(*(
            e.expressions if isinstance(e, cls) else [e] for e in exprs)))
    return expression


def simplify(expression):
    expression = flatten(expression)
    categories = get_categories(expression)
    if len(categories) == 1:
        column, kind = next(iter(categories))
        if kind == 'set':
            return _from_set(column, _to_set(expression))
        if kind == 'interval':
            return _from_interval(column, _to_interval(expression))
    if isinstance(expression, And) or isinstance(expression, Or):
        cls = expression.__class__
        # Try to collect expressions under matching categorisations.
        category_map = collections.defaultdict(list)
        for expr in expression.expressions:
            category_map[get_categories(expr)].append(expr)
        return flatten(cls(simplify(cls(expr_list)) for _, expr_list in category_map.items()))
    raise ValueError('Expressions is multi-category but not And/Or.')
