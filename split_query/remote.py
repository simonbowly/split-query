''' This module will collect tools and adapters for running remote queries. '''

from datetime import datetime
import functools

from .core.expressions import And, Or, Not, In, Eq, Le, Lt, Ge, Gt, Attribute
from .core.simplify import simplify_tree
from .core.traverse import traverse_expression


def soql_hook(obj):
    ''' Convert expressions to SOQL query string. '''
    if isinstance(obj, Attribute):
        return obj.name
    if isinstance(obj, Eq):
        return '{} = {}'.format(obj.attribute, obj.value)
    if isinstance(obj, Le):
        return '{} <= {}'.format(obj.attribute, obj.value)
    if isinstance(obj, Ge):
        return '{} >= {}'.format(obj.attribute, obj.value)
    if isinstance(obj, Lt):
        return '{} < {}'.format(obj.attribute, obj.value)
    if isinstance(obj, Gt):
        return '{} > {}'.format(obj.attribute, obj.value)
    if isinstance(obj, In):
        return '{} in ({})'.format(obj.attribute, ','.join(sorted(obj.valueset)))
    if isinstance(obj, And):
        return ' and '.join('({})'.format(s) for s in sorted(obj.clauses))
    if isinstance(obj, Or):
        return ' or '.join('({})'.format(s) for s in sorted(obj.clauses))
    if isinstance(obj, Not):
        return 'not ({})'.format(obj.clause)
    if isinstance(obj, datetime):
        return "'{}'".format(obj.isoformat())
    if isinstance(obj, str):
        return "'{}'".format(obj)
    if isinstance(obj, int) or isinstance(obj, float):
        return str(obj)
    raise ValueError('Unknown object: {}'.format(repr(obj)))


def to_soql(expression):
    ''' Convert expression object to SOQL query string. '''
    return traverse_expression(expression, hook=soql_hook)


def hook_only(attribute_names):
    def _hook_only(obj):
        if any(isinstance(obj, t) for t in [Eq, Le, Lt, Ge, Gt, In]):
            if obj.attribute.name not in attribute_names:
                return True
        return obj
    return _hook_only


def with_only_fields(expression, attributes):
    ''' Return a new expression which filters only on the given attribute names. '''
    return simplify_tree(traverse_expression(expression, hook=hook_only(attributes)))
