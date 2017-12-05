
import functools
import itertools

from .expressions import And, Attribute, Eq, Ge, Gt, In, Le, Lt, Not, Or


def traverse_expression(obj, hook):
    ''' Traverses every object in the expression: attributes, constants,
    relations, logical operators. The :hook is called on the way back up the
    tree. This is good for replacement methods, simple validators and
    converters, but a in lot of applications would ideally avoid calling
    the hook on values in expressions. This could be generalised a little
    to have an alternative hook for constants, or options for traversal
    depth. '''
    if isinstance(obj, And):
        return hook(And(traverse_expression(cl, hook) for cl in obj.clauses))
    if isinstance(obj, Or):
        return hook(Or(traverse_expression(cl, hook) for cl in obj.clauses))
    if isinstance(obj, Not):
        return hook(Not(traverse_expression(obj.clause, hook)))
    if any(isinstance(obj, _type) for _type in [Eq, Le, Lt, Ge, Gt]):
        _type = type(obj)
        return hook(_type(
            traverse_expression(obj.attribute, hook),
            traverse_expression(obj.value, hook)))
    if isinstance(obj, In):
        return hook(In(
            traverse_expression(obj.attribute, hook),
            (traverse_expression(value, hook) for value in obj.valueset)))
    return hook(obj)


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


def get_clauses(expression):
    ''' Need to fix terminology: extracts the set of things in the expression
    which are not And/Or/Not. i.e. they may take on T/F values directly as a
    result of checking a data point. '''
    if isinstance(expression, And) or isinstance(expression, Or):
        return set(itertools.chain(*(
            get_clauses(cl) for cl in expression.clauses)))
    if isinstance(expression, Not):
        return get_clauses(expression.clause)
    if expression is True or expression is False:
        return set()
    return {expression}
