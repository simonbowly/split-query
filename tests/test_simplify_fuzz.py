
from hypothesis import given
from hypothesis import strategies as st
from octo_spork.expressions import Attribute, Le, Lt, Ge, Gt, And, Or, Not

from octo_spork.logic import to_dnf, to_cnf
from octo_spork.simplify import simplify


def _link_clauses(clauses):
    linked = st.one_of(
        st.lists(clauses, min_size=1).map(And),
        st.lists(clauses, min_size=1).map(Or))
    return linked | linked.map(Not)


def inequalities(attributes, values):
    ''' Combines names and values to create an inequality clause strategy. '''
    return st.one_of(
        st.tuples(attributes, values).map(lambda r: Le(*r)),
        st.tuples(attributes, values).map(lambda r: Lt(*r)),
        st.tuples(attributes, values).map(lambda r: Ge(*r)),
        st.tuples(attributes, values).map(lambda r: Gt(*r)))


def attributes(names):
    ''' Draw from the given names to create a strategy for Attribute
    objects. If names is an iterable it will be converted to a one_of,
    otherwise names are used directly.'''
    try:
        names = st.one_of(st.just(n) for n in names)
    except:
        pass
    return names.map(Attribute)


def expressions(clauses, max_leaves):
    ''' Generate compound expressions from the given clause strategy,
    linking the tree structure with And/Or/Not branches. '''
    return st.recursive(clauses, _link_clauses, max_leaves)


inequality_clauses = inequalities(
    attributes('xyz'), values=st.integers(min_value=-10, max_value=10))


@given(expressions(inequality_clauses, max_leaves=20))
def test_simplify(expression):
    result = simplify(expression)


@given(expressions(inequality_clauses | st.booleans(), max_leaves=20))
def test_simplify(expression):
    ''' This exposes some really interesting issues. to_dnf/to_cnf are too
    slow to simplify complex clauses straight off the bat, so...
    First pass simplifier should remove any redundancies in And/Or/Not
    expressions due to boolean literals.
    e.g. And(True, c1, c2) -> And(c1, c2)
         And(False, c1, c2) -> False
         Or(True, c1, c2) -> True
         Or(False, c1, c2) -> Or(c1, c2)
    Second pass attempts domain simplification where variables can be isolated.
    CNF/DNF used only after this stage. Possibly an alternative heuristic
    function can be used to switch around common patterns?
    '''
    result = simplify(expression)
