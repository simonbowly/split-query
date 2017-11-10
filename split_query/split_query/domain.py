
import collections
import functools
import itertools

import sympy as sp

from .expressions import Float, Eq, Le, Lt, Ge, Gt, And, Or, Not


def get_attributes(expr):
    ''' Recursively search the expression, returning all attributes. '''
    if isinstance(expr, bool):
        return set()
    if isinstance(expr, Float):
        return {expr}
    if any(isinstance(expr, t) for t in [And, Or]):
        return functools.reduce(
            lambda a, b: a.union(b),
            map(get_attributes, expr.clauses))
    if isinstance(expr, Not):
        return get_attributes(expr.clause)
    if any(isinstance(expr, t) for t in [Eq, Le, Lt, Ge, Gt]):
        return get_attributes(expr.attribute)
    raise ValueError('Unhandled expression {}'.format(repr(expr)))


def _to_interval(expression):
    ''' Recursively convert an expression composed of relations into
    a sympy real number interval. Note that this does not check that the
    given expression actually constitues a 1D interval. '''
    if expression is True:
        return sp.Interval.open(-sp.S.Infinity, sp.S.Infinity)
    if expression is False:
        return sp.EmptySet()
    if isinstance(expression, Eq):
        return sp.FiniteSet(expression.value)
    if isinstance(expression, Le):
        return sp.Interval(-sp.S.Infinity, expression.value)
    if isinstance(expression, Lt):
        return sp.Interval.open(-sp.S.Infinity, expression.value)
    if isinstance(expression, Ge):
        return sp.Interval(expression.value, sp.S.Infinity)
    if isinstance(expression, Gt):
        return sp.Interval.open(expression.value, sp.S.Infinity)
    if isinstance(expression, Not):
        return _to_interval(expression.clause).complement(sp.S.Reals)
    if isinstance(expression, And):
        return functools.reduce(
            lambda x, y: x.intersection(y),
            map(_to_interval, expression.clauses))
    if isinstance(expression, Or):
        return functools.reduce(
            lambda x, y: x.union(y),
            map(_to_interval, expression.clauses))
    raise ValueError('Unhandled expression: {}'.format(repr(expression)))


def _from_interval(column, interval):
    '''  Convert sympy real number interval to logical/relational expression
    using the given attribute. '''
    if isinstance(interval, sp.Union):
        return Or(_from_interval(column, arg) for arg in interval.args)
    if isinstance(interval, sp.EmptySet):
        return False
    if isinstance(interval, sp.FiniteSet):
        expressions = [Eq(column, value) for value in interval]
        return expressions[0] if len(interval) == 1 else Or(expressions)
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


def simplify_intervals_univariate(expression):
    ''' Simplify an interval expression on a single attribute. Throws an error
    if there are multiple attributes in the expression. '''
    attributes = get_attributes(expression)
    if len(attributes) == 0:
        raise ValueError("Expression contains no attributes.")
    if len(attributes) > 1:
        raise ValueError("Expression is multivariate.")
    attribute = next(iter(attributes))
    return _from_interval(attribute, _to_interval(expression))


def simplify_domain(expression):
    ''' Descending the tree, attempt to isolate univariate expressions to
    simplify using intervals. '''
    attributes = get_attributes(expression)
    if len(attributes) == 1:
        return simplify_intervals_univariate(expression)
    if isinstance(expression, And) or isinstance(expression, Or):
        _type = type(expression)
        clauses_by_attribute = collections.defaultdict(list)
        for clause in expression.clauses:
            attrs = frozenset(get_attributes(clause))
            clauses_by_attribute[attrs].append(clause)
        new_clauses = [
            simplify_domain(_type(clauses)) if len(attrs) == 1
            else _type([simplify_domain(cl) for cl in clauses])
            for attrs, clauses in clauses_by_attribute.items()
        ]
        return _type(itertools.chain(*(
            clause.clauses if isinstance(clause, _type) else [clause]
            for clause in new_clauses)))
    if isinstance(expression, Not):
        return Not(simplify_domain(expression.clause))
    return expression
