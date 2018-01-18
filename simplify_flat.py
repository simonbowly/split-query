
import collections, itertools

from split_query.core.expressions import And, Or, Not, Le, Lt, Ge, Gt, Eq, In, Attribute


class NotIn(object):
    ''' promote this to expressions? '''

    def __init__(self, attribute, valueset):
        self.attribute = attribute
        self.valueset = valueset


def _negate_simple(cl):
    _type = type(cl)
    if _type is Le:
        return Gt(cl.attribute, cl.value)
    elif _type is Lt:
        return Ge(cl.attribute, cl.value)
    elif _type is Ge:
        return Lt(cl.attribute, cl.value)
    elif _type is Gt:
        return Le(cl.attribute, cl.value)
    elif _type is In:
        return NotIn(cl.attribute, cl.valueset)
    assert False, 'Invalid _negate_simple input: {}'.format(cl)


def _simplify_in(cl1, cl2):
    ''' Called with a pair of In/NotIn objects, returning a single clause. '''
    assert type(cl1) in [In, NotIn] and type(cl2) in [In, NotIn]
    assert cl1.attribute == cl2.attribute
    if type(cl1) is In and type(cl2) is In:
        return In(cl1.attribute, cl1.valueset.intersection(cl2.valueset))
    elif type(cl1) is NotIn and type(cl2) is NotIn:
        return Not(In(cl1.attribute, cl1.valueset.union(cl2.valueset)))
    else:
        if type(cl1) is NotIn:
            cl1, cl2 = cl2, cl1
        return In(cl1.attribute, cl1.valueset.difference(cl2.valueset))
    assert False, 'Invalid _simplify_in input: {}, {}'.format(cl1, cl2)


def _satisfies(value, inequality):
    _type = type(inequality)
    if _type is Ge:
        return value >= inequality.value
    if _type is Gt:
        return value > inequality.value
    if _type is Le:
        return value <= inequality.value
    if _type is Lt:
        return value < inequality.value
    assert False, 'Invalid _satisfies input: {}, {}'.format(value, inequality)


def simplify_flat(expression):
    ''' Simplify And([a, b, c, ...]) expressions where the clauses are simple. '''

    if type(expression) is Eq:
        return In(expression.attribute, [expression.value])

    elif type(expression) is Not:
        neg_clause = simplify_flat(expression.clause)
        if type(neg_clause) in [Le, Lt, Ge, Gt, In, Eq]:
            return _negate_simple(neg_clause)
        else:
            return Not(neg_clause)

    elif type(expression) is Or:
        return Or(simplify_flat(cl) for cl in expression.clauses)

    elif type(expression) is And:

        expression = And(simplify_flat(cl) for cl in expression.clauses)

        # Group expressions that can be simplified by attribute. Anything
        # not in scope for this algorithm is passed straight to output_clauses.
        output_clauses = []
        by_attribute = collections.defaultdict(list)
        for clause in expression.clauses:
            if type(clause) in (Le, Lt, Ge, Gt, In, NotIn):
                by_attribute[clause.attribute].append(clause)
            else:
                output_clauses.append(clause)

        # Every clause encountered in this loop is Le/Lt/Ge/Gt/In/NotIn for the
        # given attribute.
        for attribute, clauses in by_attribute.items():

            # Find least upper, greatest lower, tightest set bounds for this attribute.
            lower_bound, upper_bound, in_clause = None, None, None
            for clause in clauses:
                assert type(clause) in (Le, Lt, Ge, Gt, In, NotIn)
                if type(clause) in (Ge, Gt):
                    lower_bound = clause if lower_bound is None else max(
                        clause, lower_bound, key=lambda cl: (cl.value, type(cl) is Gt))
                elif type(clause) in (Le, Lt):
                    upper_bound = clause if upper_bound is None else min(
                        clause, upper_bound, key=lambda cl: (cl.value, type(cl) is Le))
                elif type(clause) in [In, NotIn]:
                    in_clause = clause if in_clause is None else _simplify_in(in_clause, clause)

            # Process the resulting bounds on this attribute, adding the tightest
            # bounds to output_clauses. If there are any conflicts found, the
            # process can be short-circuited, ignoring other expressions and
            # returning False.
            if in_clause is not None:
                if type(in_clause) is In:
                    if lower_bound is not None:
                        in_clause = In(attribute, [v for v in in_clause.valueset if _satisfies(v, lower_bound)])
                    if upper_bound is not None:
                        in_clause = In(attribute, [v for v in in_clause.valueset if _satisfies(v, upper_bound)])
                    if len(in_clause.valueset) == 0:
                        return False
                output_clauses.append(in_clause)
            else:
                if lower_bound is not None and upper_bound is not None:
                    if lower_bound.value == upper_bound.value:
                        if type(lower_bound) is Ge and type(upper_bound) is Le:
                            output_clauses.append(Eq(attribute, lower_bound.value))
                        else:
                            return False
                    elif lower_bound.value > upper_bound.value:
                        return False
                    else:
                        output_clauses.extend([lower_bound, upper_bound])
                elif lower_bound is not None:
                    output_clauses.append(lower_bound)
                elif upper_bound is not None:
                    output_clauses.append(upper_bound)

        # Return composed result.
        assert len(output_clauses) > 0
        return And(output_clauses) if len(output_clauses) > 1 else output_clauses[0]

    return expression






import pytest
from split_query.interface import AttributeContainer, ExpressionContainer


x = AttributeContainer(Attribute('x'))
y = AttributeContainer(Attribute('y'))


TESTCASES = [
    # No redundancy.
    ((x < 1),                       (x < 1)),
    ((x > 1) & (x < 2),             (x > 1) & (x < 2)),
    # Redundant bounds.
    ((x < 1) & (x < 0),             (x < 0)),
    ((x > 1) & (x < 2) & (x < 3),   (x > 1) & (x < 2)),
    ((x > 1) & (x < 2) & (x > 0),   (x > 1) & (x < 2)),
    # Strictly lt/gt/ should always be tighter.
    ((x > 1) & (x >= 1),            (x > 1)),
    ((x < 1) & (x <= 1),            (x < 1)),
    # Multivariate.
    (
        ((y > 1) & (y > 2) & (y > 3) & (x <= 1) & (x >= 1) & (x < 3)),
        ((y > 3) & (x == 1))),
    # Conflict cases.
    ((x > 2) & (x < 1),             False),
    ((x > 1) & (x < 1),             False),
    ((x >= 1) & (x < 1),            False),
    ((x > 1) & (x <= 1),            False),
    ((x >= 1) & (x <= 1),           (x == 1)),
    # Conflicting bounds on any variable give an overall False result.
    ((y > 1) & (y < 2) & (x > 2) & (x < 1), False),
    # Negations handled.
    (~(x > 1),                      (x <= 1)),
    (~(x >= 2),                     (x < 2)),
    (~(x < 3),                      (x >= 3)),
    (~(x <= 4),                     (x > 4)),
    (~(x > 1) & (x > 0),            (x > 0) & (x <= 1)),
    # Any unhandled expression (or, not or, etc) is included as-is.
    (
        ((x > 0) & (x > 1) & ((y > 2) | (y < 1))),
        ((x > 1) & ((y > 2) | (y < 1)))),
(
        ((x > 0) & (x > 1) & ~((y > 2) | (y < 1))),
        ((x > 1) & ~((y > 2) | (y < 1)))),
    # Set expressions.
    (
        x.isin([1, 2, 3]) & x.isin([2, 3, 4]),
        x.isin([2, 3])),
    (
        ~x.isin([1, 2, 3]) & ~x.isin([2, 3, 4]),
        ~x.isin([1, 2, 3, 4])),
    (
        x.isin([1, 2, 3]) & ~x.isin([2, 3, 4]),
        x.isin([1])),
    (x.isin([1, 2, 3]) & x.isin([4, 5, 6]), False),
    (x.isin([1, 2, 3]) & ~x.isin([1, 2, 3, 4]), False),
    # Combined bounds + sets.
    ((x == 1) & (x >= 0),           (x.isin([1]))),
    ((x == 1) & (x == 2),           False),
    (x.isin([0, 1, 2]) & (x < 2),   x.isin([0, 1])),
    (x.isin([1, 2, 3]) & (x <= 2),  x.isin([1, 2])),
    (x.isin([1, 2, 3]) & (x > 3),   False),
    # Recursive handling of nested expressions.
    (
        ((x > 1) & (x > 2)) | ((y > 1) & (y > 2)),
        (x > 2) | (y > 2)),
    (~((x > 1) & (x > 2)),          (x <= 2)),
]


@pytest.mark.parametrize('expression, simplified', TESTCASES)
def test_simplify_flat(expression, simplified):
    if isinstance(expression, ExpressionContainer):
        expression = expression.wrapped
    if isinstance(simplified, ExpressionContainer):
        simplified = simplified.wrapped
    assert simplify_flat(expression) == simplified
