
import itertools

from .domain import simplify_flat_and
from .expressions import And, Not, Or
from .logic import to_dnf_clauses


def to_dnf_simplified(expression):
    clauses = []
    for clause in to_dnf_clauses(expression):
        clause = simplify_flat_and(clause)
        if clause is True:
            return True
        elif clause is False:
            continue
        else:
            clauses.append(clause)
    if len(clauses) == 0:
        # All must have been False
        return False
    return Or(clauses)
