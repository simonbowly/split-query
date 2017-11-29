
import itertools

from .expressions import And, Not, Or
from .simplify import simplify_tree


def get_clauses(expression):
    ''' Need to fix terminology: extracts the set of things in the expression
    which are not And/Or/Not. i.e. they may take on T/F values directly as a
    result of checking a data point. '''
    if isinstance(expression, And) or isinstance(expression, Or):
        return set(itertools.chain(*(
            get_clauses(cl) for cl in expression.clauses)))
    if isinstance(expression, Not):
        return get_clauses(expression.clause)
    if expression is True or expression is False:
        return set()
    return {expression}


def substitute(expression, assignments):
    ''' Make a substitution within the expression tree using the given
    dictionary. Requires a value for every clause. '''
    if isinstance(expression, And):
        return And([substitute(cl, assignments) for cl in expression.clauses])
    if isinstance(expression, Or):
        return Or([substitute(cl, assignments) for cl in expression.clauses])
    if isinstance(expression, Not):
        return Not(substitute(expression.clause, assignments))
    if expression is True or expression is False:
        return expression
    return assignments[expression]


def truth_table(expression):
    ''' Return truth table created by assigning every T/F combination
    to clauses in the expression tree. Result is a list of tuples
    (assignment, result) where result is always True/False and assignment
    is a map from each clause to True/False. '''
    clauses = list(get_clauses(expression))
    assignments = (
        dict(zip(clauses, assignment)) for assignment in
        itertools.product([True, False], repeat=len(clauses)))
    _truth_table = [
        (assignment, simplify_tree(substitute(expression, assignment)))
        for assignment in assignments]
    assert set(result for _, result in _truth_table).issubset({True, False})
    return _truth_table


def expand_dnf(expression):
    ''' Expand to disjunctive normal form using truth table. '''
    _truth_table = truth_table(expression)
    if all(result is True for _, result in _truth_table):
        return True
    if all(result is False for _, result in _truth_table):
        return False
    return Or(
        And((
            clause if truth else Not(clause)
            for clause, truth in assignment.items()))
        for assignment, result in _truth_table
        if result is True)
