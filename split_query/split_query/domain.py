
import collections
import functools
import itertools
from datetime import datetime, timedelta, timezone

import sympy as sp

from .exceptions import SimplifyError
from .expressions import And, Attribute, Eq, Ge, Gt, In, Le, Lt, Not, Or

EPOCH = datetime(1970, 1, 1, 0, 0, 0, 0, timezone.utc)
EPOCH_NAIVE = datetime(1970, 1, 1, 0, 0, 0, 0)


def get_attributes(expr):
    ''' Recursively search the expression, returning all attributes. '''
    if isinstance(expr, bool):
        return set()
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
    raise ValueError('Unhandled expression {}'.format(repr(expr)))


def get_types(expr):
    ''' Return a set of types (of constants) in the expression. '''
    if isinstance(expr, bool):
        return set()
    if any(isinstance(expr, t) for t in [And, Or]):
        return functools.reduce(
            lambda a, b: a.union(b),
            map(get_types, expr.clauses))
    if isinstance(expr, Not):
        return get_types(expr.clause)
    if any(isinstance(expr, t) for t in [Eq, Le, Lt, Ge, Gt]):
        try:
            float(expr.value)
            return {'numeric'}
        except:
            pass
        if isinstance(expr.value, datetime):
            if expr.value.tzinfo is None:
                return {'datetime-naive'}
            else:
                return {'datetime-tz'}
    raise ValueError('Unhandled object: {}'.format(repr(expr)))


def get_expression_types(expr):
    if isinstance(expr, bool):
        return set()
    if any(isinstance(expr, t) for t in [And, Or]):
        return functools.reduce(
            lambda a, b: a.union(b),
            map(get_expression_types, expr.clauses))
    if isinstance(expr, Not):
        return get_expression_types(expr.clause)
    if any(isinstance(expr, t) for t in [Eq, Le, Lt, Ge, Gt, In]):
        return {expr.expr}
    raise ValueError('Unhandled object: {}'.format(repr(expr)))


def _convert_value(expression):
    try:
        float(expression.value)
        return expression.value
    except:
        pass
    if isinstance(expression.value, datetime):
        if expression.value.tzinfo is None:
            return (expression.value - EPOCH_NAIVE).total_seconds()
        return (expression.value - EPOCH).total_seconds()
    raise SimplifyError('Could not process: {}.'.format(str(expression.value)))


def _to_interval(expression):
    ''' Recursively convert an expression composed of relations into
    a sympy real number interval. Note that this does not check that the
    given expression actually constitutes a 1D interval. '''
    if expression is True:
        return sp.Interval.open(-sp.S.Infinity, sp.S.Infinity)
    if expression is False:
        return sp.EmptySet()
    if isinstance(expression, Eq):
        return sp.FiniteSet(_convert_value(expression))
    if isinstance(expression, Le):
        return sp.Interval(-sp.S.Infinity, _convert_value(expression))
    if isinstance(expression, Lt):
        return sp.Interval.open(-sp.S.Infinity, _convert_value(expression))
    if isinstance(expression, Ge):
        return sp.Interval(_convert_value(expression), sp.S.Infinity)
    if isinstance(expression, Gt):
        return sp.Interval.open(_convert_value(expression), sp.S.Infinity)
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


def _from_interval(column, constant_type, interval):
    '''  Convert sympy real number interval to logical/relational expression
    using the given attribute. Checks type of supplied column, converting
    sympy interval values if necessary. '''
    if constant_type == 'numeric':
        converter = float
    elif constant_type == 'datetime-tz':
        converter = lambda val: EPOCH + timedelta(microseconds=int(round(val*10**6)))
    elif constant_type == 'datetime-naive':
        converter = lambda val: EPOCH_NAIVE + timedelta(microseconds=int(round(val*10**6)))
    else:
        raise SimplifyError('Constant type: {}'.format(constant_type))
    # Process statement types
    if isinstance(interval, sp.Union):
        return Or(_from_interval(column, constant_type, arg) for arg in interval.args)
    if isinstance(interval, sp.EmptySet):
        return False
    if isinstance(interval, sp.FiniteSet):
        expressions = [Eq(column, converter(value)) for value in interval]
        return expressions[0] if len(interval) == 1 else Or(expressions)
    if interval.left == -sp.S.Infinity:
        if interval.right == sp.S.Infinity:
            return True
        if interval.right_open:
            return Lt(column, converter(interval.right))
        else:
            return Le(column, converter(interval.right))
    elif interval.right == sp.S.Infinity:
        if interval.left_open:
            return Gt(column, converter(interval.left))
        else:
            return Ge(column, converter(interval.left))
    return And([
        Gt(column, converter(interval.left)) if interval.left_open else Ge(column, converter(interval.left)),
        Lt(column, converter(interval.right)) if interval.right_open else Le(column, converter(interval.right))])


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
            _reduce_set_and, map(_to_set, expression.clauses))
    if isinstance(expression, Or):
        return functools.reduce(
            _reduce_set_or, map(_to_set, expression.clauses))
    if isinstance(expression, Not):
        if isinstance(expression.clause, In):
            return (expression.clause.valueset, '-')
    raise ValueError('Unhandled expression in _to_set')


def _from_set(column, _set):
    values, sgn = _set
    if sgn == '+':
        return In(column, values)
    else:
        return Not(In(column, values))


def simplify_intervals_univariate(expression):
    ''' Simplify an interval expression on a single attribute. Throws an error
    if there are multiple attributes in the expression. '''
    attributes = get_attributes(expression)
    if len(attributes) == 0:
        raise SimplifyError("Expression contains no attributes.")
    if len(attributes) > 1:
        raise SimplifyError("Expression is multivariate.")
    attribute = next(iter(attributes))
    # Check whether dealing with discrete or continuous filters.
    expression_types = get_expression_types(expression)
    if 'in' in expression_types:
        if len(expression_types) > 1:
            raise SimplifyError('Cannot simplify combined discrete and continuous filters')
        return _from_set(attribute, _to_set(expression))
    # Check that types are consistent for continuous domains.
    constant_types = get_types(expression)
    if len(constant_types) == 0:
        raise SimplifyError("Expression contains no constant types.")
    if len(constant_types) > 1:
        raise SimplifyError(
            "Cannot simplify expression containing multiple types: " +
            str(constant_types))
    constant_type = next(iter(constant_types))
    return _from_interval(attribute, constant_type, _to_interval(expression))


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
