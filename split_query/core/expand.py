
import itertools

from .domain import simplify_flat_and
from .expressions import And, Not, Or
from .logic import to_dnf_expand_truth_table, to_dnf_expand_heuristic, simplify_tree, is_dnf


def to_dnf_simplified(expression):
    expression = simplify_tree(expression)
    try:
        dnf = to_dnf_expand_heuristic(expression)
    except:
        dnf = to_dnf_expand_truth_table(expression)
    return simplify_tree(Or(
        simplify_flat_and(clause) for clause in dnf.clauses))
