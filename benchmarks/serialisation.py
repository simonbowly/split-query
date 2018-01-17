
import datetime
import timeit
import json
from functools import partial
from itertools import product

import msgpack
import pandas as pd
import ujson

from split_query.core import *
from split_query.core.expressions import AttributeRelation


def to_dict_list(obj):
    ''' Handle frozen things. Note that since order of iteration over a set is arbitrary,
    byte representation will not be consistent. '''
    if isinstance(obj, Attribute):
        return dict(expr='attr', name=obj.name)
    if isinstance(obj, AttributeRelation):
        return dict(
            expr=obj.__class__.__name__.lower(),
            attribute=to_dict_list(obj.attribute), value=to_dict_list(obj.value))
    if isinstance(obj, And):
        return dict(expr='and', clauses=[to_dict_list(cl) for cl in obj.clauses])
    if isinstance(obj, Or):
        return dict(expr='or', clauses=[to_dict_list(cl) for cl in obj.clauses])
    if isinstance(obj, Not):
        return dict(expr='not', clause=to_dict_list(obj.clause))
    if isinstance(obj, frozenset):
        return list(obj)
    if isinstance(obj, datetime.datetime):
        return {'dt': True, 'data': obj.isoformat(), 'naive': obj.tzinfo is None}
    return obj


def from_dict_list(obj):
    ''' Dictionary representations converted to expression objects where possible. '''
    if 'expr' in obj:
        if obj['expr'] == 'attr':
            return Attribute(obj['name'])
        if obj['expr'] == 'eq':
            return Eq(from_dict_list(obj['attribute']), obj['value'])
        if obj['expr'] == 'le':
            return Le(from_dict_list(obj['attribute']), obj['value'])
        if obj['expr'] == 'lt':
            return Lt(from_dict_list(obj['attribute']), obj['value'])
        if obj['expr'] == 'ge':
            return Ge(from_dict_list(obj['attribute']), obj['value'])
        if obj['expr'] == 'gt':
            return Gt(from_dict_list(obj['attribute']), obj['value'])
        if obj['expr'] == 'in':
            return In(from_dict_list(obj['attribute']), obj['value'])
        if obj['expr'] == 'and':
            return And([from_dict_list(cl) for cl in obj['clauses']])
        if obj['expr'] == 'or':
            return Or([from_dict_list(cl) for cl in obj['clauses']])
        if obj['expr'] == 'not':
            return Not(from_dict_list(obj['clause']))
    if 'dt' in obj and obj['dt'] is True:
        parsed = iso8601.parse_date(obj['data'])
        return parsed.replace(tzinfo=None) if obj['naive'] else parsed
    return obj


def serialise_dict(expression):
    return to_dict_list(expression)


def deserialise_dict(encoded):
    return from_dict_list(encoded)


def serialise_json(expression):
    return json.dumps(to_dict_list(expression))


def deserialise_json(encoded):
    return from_dict_list(json.loads(encoded))


def serialise_json_hook(expression):
    return json.dumps(expression, default=default)


def deserialise_json_hook(encoded):
    return json.loads(encoded, object_hook=object_hook)


def serialise_ujson(expression):
    return ujson.dumps(to_dict_list(expression))


def deserialise_ujson(encoded):
    return from_dict_list(ujson.loads(encoded))


def serialise_msgpack(expression):
    return msgpack.packb(to_dict_list(expression), use_bin_type=True)


def deserialise_msgpack(encoded):
    return from_dict_list(msgpack.unpackb(encoded, encoding='utf-8'))


def serialise_msgpack_hook(expression):
    return msgpack.packb(expression, default=default, use_bin_type=True)


def deserialise_msgpack_hook(encoded):
    return msgpack.unpackb(encoded, object_hook=object_hook, encoding='utf-8')


expression = And([
    In(Attribute('var_x'), [1, 2, 3]),
    Or([
        Le(Attribute('var_y'), 1),
        Ge(Attribute('var_y'), 2)
        ]),
    Or([
        Lt(Attribute('var_z'), 1),
        Gt(Attribute('var_z'), 2)
        ]),
    And([
        In(Attribute('var_a'), ['a', 'b', 'c']),
        Eq(Attribute('var_b'), 1)
        ])
    ])

json_encoded = serialise_json(expression)
msgpack_encoded = serialise_msgpack(expression)
dict_encoded = serialise_dict(expression)

assert deserialise_dict(dict_encoded) == expression
assert deserialise_json(json_encoded) == expression
assert deserialise_msgpack(msgpack_encoded) == expression
assert deserialise_msgpack_hook(msgpack_encoded) == expression

data = pd.DataFrame([
    dict(
        result=min(
            timeit.repeat(
                partial(
                    globals()[task + '_' + method],
                    expression if task == 'serialise' else (
                        json_encoded if 'json' in method else
                        msgpack_encoded if 'msgpack' in method else
                        dict_encoded)),
            number=10000, repeat=10)),
        method=method, task=task)
    for method, task in product(
        ['dict', 'json', 'json_hook', 'ujson', 'msgpack', 'msgpack_hook'],
        ['serialise', 'deserialise'])])

data.to_csv('serialisation_benchmarks.csv', index=False)

print(data.set_index(['method', 'task']).unstack())
