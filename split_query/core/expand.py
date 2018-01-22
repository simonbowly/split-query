
import itertools

from .algorithms import simplify_flat_and
from .expressions import And, Not, Or
from .traverse import get_clauses


def substitution_result(expression, assignments):
    if expression is True:
        return True
    if expression is False:
        return False
    if type(expression) is And:
        literals = (substitution_result(cl, assignments) for cl in expression.clauses)
        return not any(l is False for l in literals)
    if type(expression) is Or:
        literals = (substitution_result(cl, assignments) for cl in expression.clauses)
        return any(l is True for l in literals)
    if type(expression) is Not:
        literal = substitution_result(expression.clause, assignments)
        assert literal is True or literal is False
        return not literal
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
        (assignment, substitution_result(expression, assignment))
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


def expand_dnf_simplify(expression):
    expanded = expand_dnf(expression)
    if type(expanded) is Or:
        assert len(expanded.clauses) > 0
        assert all(type(cl) is And for cl in expanded.clauses)
        clauses = [simplify_flat_and(cl) for cl in expanded.clauses]
        if any(cl is True for cl in clauses):
            return True
        if all(cl is False for cl in clauses):
            return False
        clauses = list({cl for cl in clauses if cl is not False})
        assert len(clauses) > 0
        return clauses[0] if len(clauses) == 1 else Or(clauses)
    assert expanded is True or expanded is False
    return expanded
