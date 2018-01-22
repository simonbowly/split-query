''' Algorithms which rearrange logical structures linked by And/Or/Not. '''

import itertools

from .expressions import And, Or, Not


def simplify_tree(expression):
    ''' Collapse nested And/Or trees where possible and deal with any
    simple cases of boolean logic + literals. Any expression made exclusively
    of boolean literals linked by And/Or/Not should be resolved exactly. '''
    if isinstance(expression, And) or isinstance(expression, Or):
        _type = type(expression)
        clauses = (simplify_tree(clause) for clause in expression.clauses)
        clauses = itertools.chain(*(
            clause.clauses if isinstance(clause, _type) else [clause]
            for clause in clauses))
        result = _type(clauses)
        # Simple cases containing dominant or redundant boolean literals.
        if _type is And:
            if any(cl is False for cl in result.clauses):
                return False
            if all(cl is True for cl in result.clauses):
                return True
            result = And(cl for cl in result.clauses if cl is not True)
        if _type is Or:
            if any(cl is True for cl in result.clauses):
                return True
            if all(cl is False for cl in result.clauses):
                return False
            result = Or(cl for cl in result.clauses if cl is not False)
        if len(result.clauses) == 1:
            return list(result.clauses)[0]
        return result
    if isinstance(expression, Not):
        clause = simplify_tree(expression.clause)
        if clause is False:
            return True
        if clause is True:
            return False
        return Not(clause)
    return expression


def get_variables(expression):
    ''' Extracts objects which are linked in the expression by And, Or,
    Not relations. '''
    if type(expression) is And or type(expression) is Or:
        return set(itertools.chain(*(
            get_variables(cl) for cl in expression.clauses)))
    if isinstance(expression, Not):
        return get_variables(expression.clause)
    if expression is True or expression is False:
        return set()
    return {expression}


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


def truth_table_clauses(expression):
    variables = list(get_variables(expression))
    assignments = (
        dict(zip(variables, assignment)) for assignment in
        itertools.product([True, False], repeat=len(variables)))
    return (
        (
            tuple(variable if value else Not(variable) for variable, value in assignment.items()),
            substitution_result(expression, assignment))
        for assignment in assignments)


def to_dnf_clauses(expression):
    return (
        And(clause) for clause, result in truth_table_clauses(expression)
        if result is True)
