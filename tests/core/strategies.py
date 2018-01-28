
import itertools
from string import ascii_letters, printable

from hypothesis import strategies as st
from hypothesis.searchstrategy.recursive import RecursiveStrategy
import pytz

from split_query.core.expressions import (
    Attribute, And, Or, Not, Eq, Le, Lt, Ge, Gt, Eq, In)


class PrettyRecursiveStrategy(RecursiveStrategy):
    ''' Alternative to st.recursive, produces a nicer repr so it doesn't get
    in the way of reading --hypothesis-show-statistics output. '''
    def __repr__(self):
        return 'recursive'


def _link_clauses(clauses):
    ''' Used in recursive generation strategy: link branches by And/Or/Not. 
    TODO can this return e.g. Not(Eq(x, 1)) ?? '''
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
    ''' Inequality relations with numeric data. '''
    attr = Attribute(name)
    values = st.integers(min_value=-10, max_value=10)
    return st.one_of([
        values.map(lambda val: Le(attr, val)),
        values.map(lambda val: Lt(attr, val)),
        values.map(lambda val: Ge(attr, val)),
        values.map(lambda val: Gt(attr, val)),
    ])


def datetime_relation(name, timezones=None):
    ''' Inequality relations with datetime data. '''
    attr = Attribute(name)
    values = (
        st.datetimes() if timezones is None
        else st.datetimes(timezones=timezones))
    return st.one_of([
        values.map(lambda val: Le(attr, val)),
        values.map(lambda val: Lt(attr, val)),
        values.map(lambda val: Ge(attr, val)),
        values.map(lambda val: Gt(attr, val)),
    ])


def discrete_string_relation(name):
    ''' Discrete relations (In/Eq) on tag-like string data. '''
    attr = Attribute(name)
    values = st.text(printable, min_size=1, max_size=10)
    return st.one_of(
        values.map(lambda val: Eq(attr, val)),
        st.lists(values, min_size=1).map(
            lambda valueset: In(attr, valueset)))


def mixed_numeric_relation(name):
    ''' Combined inequality and discrete relations on numeric data. '''
    attr = Attribute(name)
    values = st.integers(min_value=-10, max_value=10)
    return st.one_of([
        values.map(lambda val: Eq(attr, val)),
        values.map(lambda val: Le(attr, val)),
        values.map(lambda val: Lt(attr, val)),
        values.map(lambda val: Ge(attr, val)),
        values.map(lambda val: Gt(attr, val)),
        st.lists(values, min_size=1).map(lambda val: In(attr, val)),
    ])
