
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
