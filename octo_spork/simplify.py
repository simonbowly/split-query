
import collections
import itertools

from .domain import simplify_intervals, get_attributes
from .expressions import And, Or, Not


def simplify(expression):
    ''' Attempt to reduce expressions using domain simplification techniques
    and flatten out any simple trees. Note that this aims to reduce single
    variable cases. Pure logical simplification should be done using cnf/dnf
    reduction functions. '''

    if isinstance(expression, And) or isinstance(expression, Or):
        if len(get_attributes(expression)) == 1:
            # Down to an expression of one variable, so domain simplification can
            # be applied.
            return simplify_intervals(expression)
        # Attempt to branch by splitting variables into categories.
        _type = And if isinstance(expression, And) else Or

        clauses_by_attribute = collections.defaultdict(list)
        for clause in expression.clauses:
            attributes = frozenset(get_attributes(clause))
            clauses_by_attribute[attributes].append(clause)

        if len(clauses_by_attribute) == 1 and len(expression.clauses) > 1:
            return _type([simplify(clause) for clause in expression.clauses])

        # Each clause group is simplified recursively. Attempts to flatten
        # the aggregated result if possible.
        branches = [
            simplify(_type(clauses)) if len(clauses) > 1 else simplify(clauses[0])
            for clauses in clauses_by_attribute.values()]
        return _type(itertools.chain(*(
            expr.clauses if isinstance(expr, _type) else [expr]
            for expr in branches)))
    # Negation cases: pass to domain simplifiers in single variable cases,
    # otherwise try simplification on the negated clause.
    if isinstance(expression, Not):
        if len(get_attributes(expression)) == 1:
            return simplify_intervals(expression)
        return Not(simplify(expression.clause))
    # Expression leaf node: no compound statements.
    return expression
