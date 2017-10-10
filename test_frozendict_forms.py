
import datetime
import functools

from frozendict import frozendict
import iso8601
import msgpack
import sqlalchemy


class Column(frozendict):

    def __init__(self, name):
        super().__init__(dict(expr='column', name=name))


class Equals(frozendict):

    def __init__(self, column, value):
        super().__init__(dict(expr='equals', column=column, value=value))


class And(frozendict):

    def __init__(self, expressions):
        super().__init__(dict(expr='and', data=frozenset(expressions)))


class Or(frozendict):

    def __init__(self, expressions):
        super().__init__(dict(expr='or', data=frozenset(expressions)))


class Not(frozendict):

    def __init__(self, expression):
        super().__init__(dict(expr='not', data=expression))


def msgpack_default(obj):
    ''' Handle frozen things. Note that since order of iteration over a set is arbitrary,
    byte representation will not be consistent. '''
    if isinstance(obj, frozendict):
        return dict(obj)
    if isinstance(obj, frozenset):
        return list(obj)
    if isinstance(obj, datetime.datetime):
        return {'dt': True, 'data': obj.isoformat()}
    return obj


def msgpack_object_hook(obj):
    ''' Dictionary representations converted to expression objects where possible. '''
    if 'expr' in obj:
        if obj['expr'] == 'column':
            return Column(obj['name'])
        if obj['expr'] == 'equals':
            return Equals(obj['column'], obj['value'])
        if obj['expr'] == 'and':
            return And(obj['data'])
        if obj['expr'] == 'or':
            return Or(obj['data'])
        if obj['expr'] == 'not':
            return Not(obj['data'])
    if 'dt' in obj and obj['dt'] is True:
        return iso8601.parse_date(obj['data'])
    return obj


# Defaults and object hooks included to packers.
packb = functools.partial(msgpack.packb, default=msgpack_default, use_bin_type=False)
unpackb = functools.partial(msgpack.unpackb, object_hook=msgpack_object_hook, encoding='utf-8')









import datetime

import pytest


@pytest.mark.parametrize('expr1, expr2', [
    (And(['a', 'b']), And(['b', 'a'])),
    (Or(['a', 'b']), Or(['b', 'a'])),
    ])
def test_expressions_equal(expr1, expr2):
    assert expr1 == expr2


@pytest.mark.parametrize('expr1, expr2', [
    (And(['a', 'b']), Or(['a', 'b'])),
    ])
def test_expressions_unequal(expr1, expr2):
    assert not expr1 == expr2


@pytest.mark.parametrize('expression', [
    Column('c1'),
    Equals(Column('c1'), 1),
    Equals(Column('c1'), 'haha'),
    Equals(Column('c1'), datetime.datetime.now(tz=datetime.timezone.utc)),
    And([Equals(Column('c1'), 1), Equals(Column('c2'), 2)]),
    Or([Equals(Column('c1'), 1), Equals(Column('c2'), 2)]),
    Not(Equals(Column('c1'), 1)),
    ])
def test_hashable_packable(expression):
    packed = packb(expression)
    assert isinstance(packed, bytes)
    unpacked = unpackb(packed)
    assert unpacked == expression
    assert hash(unpacked) == hash(expression)



# In[ ]:


# obj = Or([
#     And([Equals(Column('a'), 1)]),
#     Not(And([Equals(Column('b'), 2), Equals(Column('c'), 1)]))])
# print(obj)
# print(unpackb(packb(obj)))
# print(obj == unpackb(packb(obj)))
# print(packb(obj))


# In[ ]:


class SQLAlchemyConverter(object):

    def __init__(self, column_map):
        self._column_map = column_map

    def convert(self, obj):
        if isinstance(obj, Column):
            return self._column_map[obj]
        if isinstance(obj, Equals):
            return self.convert(obj['column']) == self.convert(obj['value'])
        if isinstance(obj, And):
            return sqlalchemy.sql.and_(*(self.convert(clause) for clause in obj['data']))
        if isinstance(obj, Or):
            return sqlalchemy.sql.or_(*(self.convert(clause) for clause in obj['data']))
        if isinstance(obj, Not):
            return sqlalchemy.sql.not_(self.convert(obj['data']))
        return obj


# # In[ ]:


# metadata = sqlalchemy.MetaData()
# table = sqlalchemy.Table('mytable', metadata,
#     sqlalchemy.Column('a', sqlalchemy.Integer),
#     sqlalchemy.Column('b', sqlalchemy.Integer),
#     sqlalchemy.Column('c', sqlalchemy.Integer))
# converter = SQLAlchemyConverter({Column(colname): sqlcol for colname, sqlcol in table.columns.items()})

# print(str(sql.select(columns=table.columns, whereclause=converter.convert(obj))))


# # In[ ]:


# str(table.c.a.in_([1, 2, 3]))


# # In[ ]:


# from datetime import datetime


# # In[ ]:


# msgpack.unpackb(msgpack.packb(datetime.now().isoformat()))


# # In[ ]:


# import iso8601


# # In[ ]:


# iso8601.parse_date('2017-10-10T18:32:29.798183')


# # In[ ]:


# datetime.now()

