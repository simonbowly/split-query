
import itertools
from string import ascii_letters, printable

from hypothesis import strategies as st
from hypothesis.searchstrategy.recursive import RecursiveStrategy
import pytz

from split_query.core.expressions import (
    Attribute, And, Or, Not, Eq, Le, Lt, Ge, Gt, Eq, In)


def unique_expressions():
    ''' All pairwise comparisons of elements in this generator should be found
    to be unequal. This is an important property of the immutable expression
    objects to ensure they can be sensibly used as unique descriptions of data.
    '''
    yield Attribute('x')
    for relation, attr, value in itertools.product(
            [Le, Lt, Ge, Gt, Eq], ['x', 'y'], [1, 2]):
        yield relation(attr, value)
    yield In(Attribute('x'), ['a', 'b'])
    yield And(['a', 'b'])
    yield And(['a', 'c'])
    yield Or(['a', 'b'])
    yield Or(['a', 'c'])
    yield Not('a')
    yield Not('b')


class PrettyRecursiveStrategy(RecursiveStrategy):
    ''' Alternative to st.recursive, produces a nicer repr so it doesn't get
    in the way of reading --hypothesis-show-statistics output. '''
    def __repr__(self):
        return 'recursive'


def _link_clauses(clauses):
    ''' Used in recursive generation strategy: link branches by And/Or/Not. '''
    linked = st.one_of(
        st.lists(clauses, min_size=1).map(And),
        st.lists(clauses, min_size=1).map(Or))
    return linked | linked.map(Not)


def expression_recursive(variables, max_leaves):
    ''' Build trees using recursive (in its quieter form). '''
    return PrettyRecursiveStrategy(variables, _link_clauses, max_leaves)


def expression_trees(variables, max_depth, min_width, max_width):
    ''' Alternative to recursive/link_clauses, which limits by width and depth
    rather than leaves. Still results in invalid expressions, not sure why.
    Build the strategy upfront to the given depth. '''
    elements = st.one_of(variables, variables.map(Not))
    for _ in range(max_depth):
        clauses = st.lists(elements, min_size=min_width, max_size=max_width)
        elements  = st.one_of(clauses.map(And), clauses.map(Or))
    return elements


def continuous_numeric_relation(name):
    ''' Continuous numeric relations on the given attribute name. '''
    attr = Attribute(name)
    values = st.integers(min_value=-10, max_value=10)
    return st.one_of([
        values.map(lambda val: Eq(attr, val)),
        values.map(lambda val: Le(attr, val)),
        values.map(lambda val: Lt(attr, val)),
        values.map(lambda val: Ge(attr, val)),
        values.map(lambda val: Gt(attr, val)),
    ])


def datetime_relation(name, timezones=None):
    ''' Datetime relations on the given attribute name. '''
    attr = Attribute(name)
    values = (
        st.datetimes() if timezones is None
        else st.datetimes(timezones=timezones))
    return st.one_of([
        values.map(lambda val: Eq(attr, val)),
        values.map(lambda val: Le(attr, val)),
        values.map(lambda val: Lt(attr, val)),
        values.map(lambda val: Ge(attr, val)),
        values.map(lambda val: Gt(attr, val)),
    ])


def discrete_relation(name):
    ''' Discrete relations on the given attribute name. '''
    attr = Attribute(name)
    return st.lists(st.integers(min_value=-10, max_value=10), min_size=1).map(
        lambda valueset: In(attr, valueset))


def structured_3d_expressions(max_leaves=100):
    ''' Generate expressions which are relevant for testing simplification and queries.
    The result can contain the following relations:

        Continuous Eq, Lt, Le, Gt, Ge numeric filters on 'x'.
        Continuous Eq, Lt, Le, Gt, Ge datetime filters on 'datetime'.
        Discrete In filters on 'id'.

    '''
    relations = st.one_of(
        continuous_numeric_relation('x'),
        discrete_relation('id'),
        datetime_relation('dt'),
        datetime_relation('dt-tz', timezones=st.just(pytz.utc)))
    return expression_recursive(relations, max_leaves=max_leaves)
