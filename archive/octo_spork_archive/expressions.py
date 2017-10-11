
def flatten(expression):
    if isinstance(expression, And) or isinstance(expression, Or):
        if len(expression.expressions) == 1:
            return next(iter(expression.expressions))
        cls = expression.__class__
        exprs = map(flatten, expression.expressions)
        return cls(itertools.chain(*(
            e.expressions if isinstance(e, cls) else [e] for e in exprs)))
    return expression


def simplify(expression):
    expression = flatten(expression)
    categories = get_categories(expression)
    if len(categories) == 1:
        column, kind = next(iter(categories))
        if kind == 'set':
            return _from_set(column, _to_set(expression))
        if kind == 'interval':
            return _from_interval(column, _to_interval(expression))
    if isinstance(expression, And) or isinstance(expression, Or):
        cls = expression.__class__
        # Try to collect expressions under matching categorisations.
        category_map = collections.defaultdict(list)
        for expr in expression.expressions:
            category_map[get_categories(expr)].append(expr)
        return flatten(cls(simplify(cls(expr_list)) for _, expr_list in category_map.items()))
    raise ValueError('Expressions is multi-category but not And/Or.')
