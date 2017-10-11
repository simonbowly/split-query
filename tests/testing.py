
from string import printable

from hypothesis import strategies as st

from octo_spork.expressions import Attribute, Eq, Le, Lt, Ge, Gt, And, Or, Not


def st_expressions(names=printable, max_leaves=100):
    ''' Creates an expression generation strategy for hypothesis. '''

    # Construct named attributes from text.
    attribute = st.text(names, min_size=1).map(lambda name: Attribute(name))

    # Left to right relation generator. Chooses an attribute, comparison
    # operator and value to construct the relation.
    pos_relations = st.tuples(
        st.one_of(st.just(r) for r in [Eq, Le, Lt, Ge, Gt]), attribute,
        st.integers(min_value=-10, max_value=10)).map(
            lambda r: r[0](r[1], r[2]))

    # Strategy which adds negation to some relations.
    relations = st.tuples(
        st.just(Not) | st.none(), pos_relations).map(
            lambda v: v[1] if v[0] is None else v[0](v[1]))

    def not_and(clauses):
        return Not(And(clauses))

    def not_or(clauses):
        return Not(Or(clauses))

    def clause_link(clauses):
        ''' Combine relation generating strategy with choice of And/Or as a
        linking method. '''
        link_choice = st.one_of(
            st.just(r) for r in [And, Or, not_and, not_or])
        return st.tuples(link_choice, st.lists(clauses, min_size=1)).map(
            lambda v: v[0](v[1]))
    # TODO remove min/max size restrictions

    # Recursive constructor of expressions from relations linked by and/or.
    return st.recursive(relations, clause_link, max_leaves=max_leaves)
