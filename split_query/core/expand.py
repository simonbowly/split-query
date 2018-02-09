
import itertools

from .domain import simplify_flat_and
from .expressions import And, Not, Or
from .logic import *

# Issue: heuristic returns overlapping partials?

def to_dnf_simplified(expression, use_truth_table=False):
    if use_truth_table:
        # Force full expansion (for independent blocks).
        dnf = to_dnf_expand_truth_table(expression)
    else:
        expression = simplify_tree(expression)
        if is_simple(expression):
            # Really just needs normalisation.
            return simplify_flat_and(And([expression]))
        elif is_flat_and(expression):
            return simplify_flat_and(expression)
        elif is_dnf(expression):
            dnf = expression
        else:
            try:
                dnf = to_dnf_expand_heuristic(expression)
            except:
                # Fallback to the slow way.
                dnf = to_dnf_expand_truth_table(expression)
    return simplify_tree(Or(
        simplify_flat_and(clause) if type(clause) is And else clause
        for clause in dnf.clauses))
