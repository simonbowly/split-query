''' Serialisation hooks, compatible with msgpack and json. Converts expressions
based on frozenset and frozendict classes into lists and dicts. '''

import datetime

import iso8601

from .expressions import (
    Attribute, And, Or, Not,
    ConditionalRelation, Eq, Ge, Gt, In, Le, Lt)


def default(obj):
    ''' Handle frozen things. Note that since order of iteration over a set is arbitrary,
    byte representation will not be consistent. '''
    if isinstance(obj, Attribute):
        return dict(expr='attr', name=obj.name)
    if isinstance(obj, ConditionalRelation):
        return dict(
            expr=obj.__class__.__name__.lower(),
            attribute=obj.attribute, value=obj.value)
    if isinstance(obj, And):
        return dict(expr='and', clauses=obj.clauses)
    if isinstance(obj, Or):
        return dict(expr='or', clauses=obj.clauses)
    if isinstance(obj, Not):
        return dict(expr='not', clause=obj.clause)
    if isinstance(obj, datetime.datetime):
        return {'dt': True, 'data': obj.isoformat(), 'naive': obj.tzinfo is None}
    return obj


def object_hook(obj):
    ''' Dictionary representations converted to expression objects where possible. '''
    if 'expr' in obj:
        if obj['expr'] == 'attr':
            return Attribute(obj['name'])
        if obj['expr'] == 'eq':
            return Eq(obj['attribute'], obj['value'])
        if obj['expr'] == 'le':
            return Le(obj['attribute'], obj['value'])
        if obj['expr'] == 'lt':
            return Lt(obj['attribute'], obj['value'])
        if obj['expr'] == 'ge':
            return Ge(obj['attribute'], obj['value'])
        if obj['expr'] == 'gt':
            return Gt(obj['attribute'], obj['value'])
        if obj['expr'] == 'in':
            return In(obj['attribute'], obj['value'])
        if obj['expr'] == 'and':
            return And(obj['clauses'])
        if obj['expr'] == 'or':
            return Or(obj['clauses'])
        if obj['expr'] == 'not':
            return Not(obj['clause'])
    if 'dt' in obj and obj['dt'] is True:
        parsed = iso8601.parse_date(obj['data'])
        return parsed.replace(tzinfo=None) if obj['naive'] else parsed
    return obj
