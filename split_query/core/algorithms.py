
import collections
import itertools

from split_query.core.expressions import And, Or, Not, Le, Lt, Ge, Gt, Eq, In, Attribute


class NotIn(object):
    ''' promote this to expressions? '''

    def __init__(self, attribute, valueset):
        self.attribute = attribute
        self.valueset = valueset


def _simplify_in(cl1, cl2):
    ''' Called with a pair of In/NotIn objects, returning a single clause. '''
    assert type(cl1) in [In, NotIn] and type(cl2) in [In, NotIn]
    assert cl1.attribute == cl2.attribute
    if type(cl1) is In and type(cl2) is In:
        return In(cl1.attribute, cl1.valueset.intersection(cl2.valueset))
    elif type(cl1) is NotIn and type(cl2) is NotIn:
        return NotIn(cl1.attribute, cl1.valueset.union(cl2.valueset))
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


def _normalise_input(clause):
    if type(clause) is Eq:
        return In(clause.attribute, [clause.value])
    if type(clause) is Not:
        sub = clause.clause
        if type(sub) is Ge:
            return Lt(sub.attribute, sub.value)
        if type(sub) is Gt:
            return Le(sub.attribute, sub.value)
        if type(sub) is Le:
            return Gt(sub.attribute, sub.value)
        if type(sub) is Lt:
            return Ge(sub.attribute, sub.value)
        if type(sub) is In:
            return NotIn(sub.attribute, sub.valueset)
        if type(sub) is Eq:
            return NotIn(sub.attribute, {sub.value})
    return clause


def _normalise_output(clause):
    if type(clause) is In and len(clause.valueset) == 1:
        return Eq(clause.attribute, next(iter(clause.valueset)))
    if type(clause) is NotIn:
        if len(clause.valueset) == 1:
            return Not(Eq(clause.attribute, next(iter(clause.valueset))))
        else:
            return Not(In(clause.attribute, clause.valueset))
    return clause


HANDLED_CLAUSES = (Le, Lt, Ge, Gt, In, NotIn)


def simplify_flat_and(expression):
    ''' Simplify Le/Lt/Ge/Gt/Eq/In expressions joined by And clause. '''

    if type(expression) is And:

        # Group expressions that can be simplified by attribute. Anything
        # not in scope for this algorithm is passed straight to output_clauses.
        by_attribute = collections.defaultdict(list)
        other_clauses = []
        for clause in (_normalise_input(cl) for cl in expression.clauses):
            if type(clause) in HANDLED_CLAUSES:
                by_attribute[clause.attribute].append(clause)
            else:
                other_clauses.append(clause)

        # Every clause encountered in this loop is Le/Lt/Ge/Gt/In for the
        # given attribute.
        output_clauses = []
        for attribute, clauses in by_attribute.items():

            # Find least upper, greatest lower, tightest set bounds for this attribute.
            lower_bound, upper_bound, in_clause = None, None, None
            for clause in clauses:
                assert type(clause) in HANDLED_CLAUSES
                if type(clause) in (Ge, Gt):
                    lower_bound = clause if lower_bound is None else max(
                        clause, lower_bound, key=lambda cl: (cl.value, type(cl) is Gt))
                elif type(clause) in (Le, Lt):
                    upper_bound = clause if upper_bound is None else min(
                        clause, upper_bound, key=lambda cl: (cl.value, type(cl) is Le))
                elif type(clause) in (In, NotIn):
                    in_clause = clause if in_clause is None else _simplify_in(in_clause, clause)

            # Process the resulting bounds on this attribute, adding the tightest
            # bounds to output_clauses. If there are any conflicts found, the
            # process can be short-circuited, ignoring other expressions and
            # returning False.
            if in_clause is not None:
                assert type(in_clause) in (In, NotIn)
                if lower_bound is not None:
                    in_clause = In(attribute, [v for v in in_clause.valueset if _satisfies(v, lower_bound)])
                if upper_bound is not None:
                    in_clause = In(attribute, [v for v in in_clause.valueset if _satisfies(v, upper_bound)])
                if len(in_clause.valueset) == 0:
                    return False
                output_clauses.append(in_clause)
            else:
                assert lower_bound is None or type(lower_bound) in (Ge, Gt)
                assert upper_bound is None or type(upper_bound) in (Le, Lt)
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
        output_clauses = [_normalise_output(cl) for cl in output_clauses + other_clauses]
        assert len(output_clauses) > 0
        if any(cl is False for cl in output_clauses):
            return False
        output_clauses = [cl for cl in output_clauses if cl is not True]
        if len(output_clauses) == 0:   # Must have been all True
            return True
        return And(output_clauses) if len(output_clauses) > 1 else output_clauses[0]

    return _normalise_output(_normalise_input(expression))
