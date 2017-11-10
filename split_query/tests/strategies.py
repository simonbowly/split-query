
from hypothesis import given
from hypothesis import strategies as st

from split_query.expressions import Float, Eq, Le, Lt, Ge, Gt, And, Or, Not


def attributes(dtype, names):
    ''' Return a strategy generating Float attributes from the given name
    generation strategy. If a list of names is provided, they will be used
    to create a one_of strategy for the attribute names. '''
    try:
        names = st.one_of(st.just(n) for n in names)
    except:
        pass
    return names.map(dtype)


def inequalities(attributes, values):
    ''' Return a strategy which generates inequality relations from the given
    attribute and value generation strategies. '''
    return st.one_of(
        st.tuples(attributes, values).map(lambda r: Le(*r)),
        st.tuples(attributes, values).map(lambda r: Lt(*r)),
        st.tuples(attributes, values).map(lambda r: Ge(*r)),
        st.tuples(attributes, values).map(lambda r: Gt(*r)))


def relations(attributes, values):
    ''' Return a strategy which generates any relation type from the given
    attribute and value generation strategies. '''
    return st.one_of(
        st.tuples(attributes, values).map(lambda r: Eq(*r)),
        st.tuples(attributes, values).map(lambda r: Le(*r)),
        st.tuples(attributes, values).map(lambda r: Lt(*r)),
        st.tuples(attributes, values).map(lambda r: Ge(*r)),
        st.tuples(attributes, values).map(lambda r: Gt(*r)))


def _link_clauses(clauses):
    ''' Used in recursive generation strategy, linking branches by And/Or/Not. '''
    linked = st.one_of(
        st.lists(clauses, min_size=1).map(And),
        st.lists(clauses, min_size=1).map(Or))
    return linked | linked.map(Not)


def expressions(clauses, max_leaves):
    ''' Return a strategy which generates expression trees (linked with
    And/Or/Not) from the given relation generation strategy. '''
    return st.recursive(clauses, _link_clauses, max_leaves)


def float_expressions(names, max_leaves=100, literals=True):
    clauses = relations(attributes(Float, names), st.integers(-10, 10))
    if literals:
        clauses = clauses | st.booleans()
    return expressions(clauses, max_leaves=max_leaves)
