
import collections

from .domain import simplify_sets, simplify_intervals
from .functions import And, Or, get_categories
from .logic import to_cnf, to_dnf


def simplify(expression):
    expression = to_dnf(expression)
    expression = _simplify(expression)
    return to_dnf(expression)


def _simplify(expression):
    # expression = to_cnf(expression)
    categories = get_categories(expression)
    # Single column expressions can be passed to appropriate domain simplifiers.
    if len(categories) == 1:
        column, kind = next(iter(categories))
        if kind == 'set':
            return simplify_sets(expression)
        if kind == 'interval':
            return simplify_intervals(expression)
    # Clause expressions need to be split by category.
    if isinstance(expression, And) or isinstance(expression, Or):
        cls = expression.__class__
        # Try to collect expressions under matching categorisations.
        category_map = collections.defaultdict(list)
        for expr in expression.expressions:
            category_map[get_categories(expr)].append(expr)
        partials = (
            expr_list[0] if len(expr_list) == 1 else cls(expr_list)
            for _, expr_list in category_map.items())
        return cls(
            simplify(e) if e != expression else e
            for e in partials)
    raise ValueError('Expressions is somehow multi-category but not And/Or.')
    # Still a lot of recursion issues, which shouldn't exist as everything is depth 2...
    # Maybe better to write this in explicit form for dnf/cnf simplifications?
