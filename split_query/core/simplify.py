
import collections
import functools
import itertools
from datetime import datetime, timedelta, timezone

import sympy as sp

from .expressions import And, Attribute, Eq, Ge, Gt, In, Le, Lt, Not, Or
from .traverse import get_attributes, traverse_expression

EPOCH = datetime(1970, 1, 1, 0, 0, 0, 0, timezone.utc)
EPOCH_NAIVE = datetime(1970, 1, 1, 0, 0, 0, 0)


class SimplifyError(Exception):
    pass


def simplify_tree(expression):
    ''' Collapse nested And/Or trees where possible and deal with any
    simple cases of boolean logic + literals. Any expression made exclusively
    of boolean literals linked by And/Or/Not should be resolved exactly. '''
    if isinstance(expression, And) or isinstance(expression, Or):
        _type = type(expression)
        clauses = (simplify_tree(clause) for clause in expression.clauses)
        clauses = itertools.chain(*(
            clause.clauses if isinstance(clause, _type) else [clause]
            for clause in clauses))
        result = _type(clauses)
        # Simple cases containing dominant or redundant boolean literals.
        if _type is And:
            if any(cl is False for cl in result.clauses):
                return False
            if all(cl is True for cl in result.clauses):
                return True
            result = And(cl for cl in result.clauses if cl is not True)
        if _type is Or:
            if any(cl is True for cl in result.clauses):
                return True
            if all(cl is False for cl in result.clauses):
                return False
            result = Or(cl for cl in result.clauses if cl is not False)
        if len(result.clauses) == 1:
            return list(result.clauses)[0]
        return result
    if isinstance(expression, Not):
        clause = simplify_tree(expression.clause)
        if clause is False:
            return True
        if clause is True:
            return False
        return Not(clause)
    return expression


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


def hook(obj, attribute):
    ''' Some of the literal cases here should probably be dealt with
    by running simplify_tree first. '''

    if isinstance(obj, In) and len(obj.valueset) == 0:
        return False

    if isinstance(obj, Not) and obj.clause is False:
        return True

    if isinstance(obj, Or):

        clauses = obj.clauses
        if any(cl is True for cl in clauses):
            return True
        if all(cl is False for cl in clauses):
            return False
        clauses = [cl for cl in clauses if cl is not False]

        in_ = [cl for cl in clauses if isinstance(cl, In)]
        notin = [cl for cl in clauses if isinstance(cl, Not)]
        assert len(in_) + len(notin) == len(clauses)

        in_valueset = set() if len(in_) == 0 else functools.reduce(
            lambda a, b: a.union(b),
            (cl.valueset for cl in in_))
        notin_valueset = set() if len(notin) == 0 else functools.reduce(
            lambda a, b: a.intersection(b),
            (cl.clause.valueset for cl in notin))

        if len(notin) > 0:
            final = notin_valueset - in_valueset
            if len(final) == 0:
                return True
            return Not(In(attribute, final))
        else:
            if len(in_valueset) == 0:
                return True
            return In(attribute, in_valueset)

    if isinstance(obj, And):

        clauses = obj.clauses
        if any(cl is False for cl in clauses):
            return False
        if all(cl is True for cl in clauses):
            return True
        clauses = [cl for cl in clauses if cl is not True]

        in_ = [cl for cl in clauses if isinstance(cl, In)]
        notin = [cl for cl in clauses if isinstance(cl, Not)]
        assert len(in_) + len(notin) == len(clauses)

        in_valueset = set() if len(in_) == 0 else functools.reduce(
            lambda a, b: a.intersection(b),
            (cl.valueset for cl in in_))
        notin_valueset = set() if len(notin) == 0 else functools.reduce(
            lambda a, b: a.union(b),
            (cl.clause.valueset for cl in notin))

        if len(in_) > 0:
            final = in_valueset - notin_valueset
            if len(final) == 0:
                return False
            return In(attribute, final)
        else:
            if len(notin_valueset) == 0:
                return False
            return Not(In(attribute, notin_valueset))

    return obj


def simplify_set_univariate(attribute, expression):
    return traverse_expression(expression, hook=functools.partial(
        hook, attribute=attribute))
    # return _from_set(attribute, _to_set(expression))


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
        return simplify_set_univariate(attribute, expression)
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


def _main_simplify_domain(expression):
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


def simplify_domain(expression):
    return simplify_tree(_main_simplify_domain(expression))
