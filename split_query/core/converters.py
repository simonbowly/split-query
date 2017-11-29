
from datetime import datetime

from .expressions import And, Or, Not, In, Eq, Le, Lt, Ge, Gt, Attribute


def convert_expression(obj, hook):
    ''' Modelled on msgpack (or my assumption on how it works). This function
    will traverse the tree of everything that it knows how to navigate. The hook
    is always called on the way back up, so it can assume any parts of the
    expression further down in the tree have already been processed. Since all
    the expression types are just containers (frozendicts), they will not
    complain about nonsensical intermediary states. '''
    if isinstance(obj, And):
        return hook(And(convert_expression(cl, hook) for cl in obj.clauses))
    if isinstance(obj, Or):
        return hook(Or(convert_expression(cl, hook) for cl in obj.clauses))
    if isinstance(obj, Not):
        return hook(Not(convert_expression(obj.clause, hook)))
    if any(isinstance(obj, _type) for _type in [Eq, Le, Lt, Ge, Gt]):
        _type = type(obj)
        return hook(_type(
            convert_expression(obj.attribute, hook),
            convert_expression(obj.value, hook)))
    if isinstance(obj, In):
        return hook(In(
            convert_expression(obj.attribute, hook),
            (convert_expression(value, hook) for value in obj.valueset)))
    return hook(obj)


def substitute_attributes(obj, substitutions):
    ''' Replace named attributes if they are in the given map. '''
    if isinstance(obj, Attribute) and obj in substitutions:
        return substitutions[obj]
    return obj


def in_to_or(obj):
    ''' Expand In expressions to Or(Eq). '''
    if isinstance(obj, In):
        return Or([Eq(obj.attribute, value) for value in obj.valueset])
    return obj


def soql(obj):
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


def map_to_ids(obj, attribute_map):
    if isinstance(obj, Eq) and obj.attribute in attribute_map:
        mapped, value_map = attribute_map[obj.attribute]
        return Eq(mapped, value_map[obj.value])
    if isinstance(obj, In) and obj.attribute in attribute_map:
        mapped, value_map = attribute_map[obj.attribute]
        return In(mapped, (value_map[v] for v in obj.valueset))
    return obj
