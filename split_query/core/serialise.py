''' Serialisation hooks, compatible with msgpack and json. Converts expressions
based on frozenset and frozendict classes into lists and dicts. '''

import datetime

import frozendict
import iso8601

from .expressions import And, Attribute, Eq, Ge, Gt, In, Le, Lt, Not, Or


def default(obj):
    ''' Handle frozen things. Note that since order of iteration over a set is arbitrary,
    byte representation will not be consistent. '''
    if isinstance(obj, frozendict.frozendict):
        return dict(obj)
    if isinstance(obj, frozenset):
        return list(obj)
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
            return In(obj['attribute'], obj['valueset'])
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
