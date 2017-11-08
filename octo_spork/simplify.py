
import collections
import itertools

from .domain import simplify_intervals, get_attributes
from .expressions import And, Or, Not


def simplify(expression):
    ''' Attempt to reduce expressions using domain simplification techniques
    and flatten out any simple trees. Note that this aims to reduce single
    variable cases. Pure logical simplification should be done using cnf/dnf
    reduction functions. '''
    if isinstance(expression, And):
        # Handle any simple literal cases (all True, any False)
        # and remove redundancy e.g. And(True, c1, c2) = And(c1, c2)
        if all(clause is True for clause in expression.clauses):
            return True
        if any(clause is False for clause in expression.clauses):
            return False
        if any(clause is True for clause in expression.clauses):
            return simplify(And([
                clause for clause in expression.clauses
                if clause is not True]))
    if isinstance(expression, Or):
        # Handle any simple literal cases (all False, any True)
        # and remove redundancy e.g. Or(False, c1, c2) = Or(c1, c2)
        if all(clause is False for clause in expression.clauses):
            return False
        if any(clause is True for clause in expression.clauses):
            return True
        if any(clause is False for clause in expression.clauses):
            return simplify(Or([
                clause for clause in expression.clauses
                if clause is not False]))
    if isinstance(expression, And) or isinstance(expression, Or):
        if len(expression.clauses) == 1:
            # Remove trivial nests.
            return simplify(next(iter(expression.clauses)))
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
        _clause = simplify(expression.clause)
        if _clause is True:
            return False
        if _clause is False:
            return True
        return Not(_clause)
    # Expression leaf node: no compound statements.
    return expression
