
from collections import defaultdict
from itertools import product, chain
from .core import And, Or, Not, In, Eq, Le, Lt, Ge, Gt, to_dnf_simplified, simplify_tree


def extract_parameters(expression, parameters):
    ''' Given an expression in the form E or And(E1, E2, E3), extract arguments
    for a data extraction function. The expression must be domain simplified.
    Returns a list of expressions (may be more than one if the parameters are
    split) and the corresponding extracted arguments.

    Expression:
        Must be a single In/Eq/Le/Lt/Ge/Gt expression or a flat And()
        composition of them.

    Supported parameters:
        - dict(attr='x', type='tag', key='xtags', single=False)
        Extracts the In(x, values) relation, passes values with key 'xtags'.
        - dict(attr='x', type='tag', key='xtag', single=True)
        Separates the values of the In clause to a separate result for each
        value, with the key 'xtag'.
        - dict(attr='y', type='range', key_lower='from_y', key_upper='to_y')
        Extract bounds from Ge/Gt/Le/Lt expressions, pass with given keys.

    '''

    if len(parameters) == 0:
        raise ValueError('At least one parameter must be specified.')

    if isinstance(expression, And):
        attribute_mapping = defaultdict(list)
        for clause in expression.clauses:
            attribute_mapping[clause.attribute.name].append(clause)
    elif any(isinstance(expression, t) for t in [In, Eq, Le, Lt, Ge, Gt]):
        attribute_mapping = {expression.attribute.name: [expression]}

    results = None

    for parameter in parameters:
        clauses = attribute_mapping[parameter['attr']]

        if parameter['type'] == 'tag':
            assert len(clauses) == 1
            clause = next(iter(clauses))
            assert type(clause) in (In, Eq)
            valueset = clause.valueset if type(clause) is In else [clause.value]
            if parameter['single']:
                new_results = [
                    ([In(clause.attribute, [value])], {parameter['key']: value})
                    for value in valueset]
            else:
                new_results = [([In(clause.attribute, valueset)], {parameter['key']: set(valueset)})]

        elif parameter['type'] == 'range':
            if len(clauses) != 2:
                raise ValueError(repr(clauses))
            clause1, clause2 = sorted(clauses, key=lambda obj: obj.__class__.__name__)
            assert isinstance(clause1, Ge) or isinstance(clause1, Gt)
            assert isinstance(clause2, Le) or isinstance(clause2, Lt)
            if 'round_down' in parameter:
                lower, upper = clause1.value, clause2.value
                assert lower < upper
                bounds = []
                current = parameter['round_down'](lower)
                while True:
                    _next = parameter['offset'](current)
                    bounds.append((current, _next))
                    current = _next
                    if current >= upper:
                        break
                new_results = [
                    (
                        [Ge(clause1.attribute, low), Le(clause2.attribute, high)], {
                        parameter['key_lower']: low,
                        parameter['key_upper']: high})
                    for low, high in bounds]
            else:
                new_results = [(
                    [Ge(clause1.attribute, clause1.value), Le(clause2.attribute, clause2.value)], {
                    parameter['key_lower']: clause1.value,
                    parameter['key_upper']: clause2.value})]

        else:
            raise ValueError()

        if results is None:
            results = new_results
        else:
            results = [
                (clauses1 + clauses2, dict(kwargs1, **kwargs2))
                for (clauses1, kwargs1), (clauses2, kwargs2) in product(results, new_results)]

    return [
        (clauses[0] if len(clauses) == 1 else And(clauses), kwargs)
        for clauses, kwargs in results]


def split_parameters(expression, parameters):
    ''' Adds some wrapping around extract_parameters to trim unnecessary
    filters and expand to DNF form. '''

    # Retain only filters which affect the given parameters.
    attributes = [param['attr'] for param in parameters]

    # Break query into subqueries for extract_parameters.
    expanded = to_dnf_simplified(expression, use_truth_table=True)
    if isinstance(expanded, And):
        subqueries = [expanded]
    elif isinstance(expanded, Or):
        subqueries = list(expanded.clauses)
    else:
        raise ValueError('Expression may be too broad.')

    # Creates a generator broken down into DNF clause subqueries, then by
    # parameter settings. Should be no overlap, since DNF gives disjoint
    # subqueries (TODO CONFIRM THIS SO OVERLAP DOES NOT OCCUR)
    return chain(*(
        extract_parameters(subquery, parameters)
        for subquery in subqueries))
