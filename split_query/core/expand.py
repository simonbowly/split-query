
import itertools

from .domain import simplify_flat_and
from .expressions import And, Not, Or
from .logic import *


def to_dnf_simplified(expression):
    expression = simplify_tree(expression)
    if is_simple(expression):
        return simplify_flat_and(And([expression]))     # Really just needs normalisation.
    elif is_flat_and(expression):
        return simplify_flat_and(expression)
    elif is_dnf(expression):
        dnf = expression
    else:
        try:
            dnf = to_dnf_expand_heuristic(expression)
        except:
            dnf = to_dnf_expand_truth_table(expression)
    return simplify_tree(Or(
        simplify_flat_and(clause) if type(clause) is And else clause
        for clause in dnf.clauses))
