'''
Algorithms to simplify domain relationships in conditional expressions.
    - simplify_flat_and
'''

import collections

from .expressions import And, Not, Le, Lt, Ge, Gt, Eq, In


# Placeholder expression object, never returned as part of an expression.
NotIn = collections.namedtuple('NotIn', ['attribute', 'valueset'])


def _simplify_in(cl1, cl2):
    ''' Reduce And(cl1, cl2) to a single relation where both inputs are
    In/NotIn relations. '''
    assert type(cl1) in [In, NotIn] and type(cl2) in [In, NotIn]
    assert cl1.attribute == cl2.attribute
    if type(cl1) is In and type(cl2) is In:
        return In(cl1.attribute, set(cl1.valueset).intersection(set(cl2.valueset)))
    elif type(cl1) is NotIn and type(cl2) is NotIn:
        return NotIn(cl1.attribute, set(cl1.valueset).union(set(cl2.valueset)))
    else:
        if type(cl1) is NotIn:
            cl1, cl2 = cl2, cl1
        return In(cl1.attribute, set(cl1.valueset).difference(set(cl2.valueset)))
    raise ValueError('Invalid _simplify_in input: {}, {}'.format(cl1, cl2))


def _satisfies(value, inequality):
    ''' Return whether :value satisfies the relation given by :inequality.
    Raises ValueError if :inequality is not an inequality relation. '''
    _type = type(inequality)
    if _type is Ge:
        return value >= inequality.value
    if _type is Gt:
        return value > inequality.value
    if _type is Le:
        return value <= inequality.value
    if _type is Lt:
        return value < inequality.value
    raise ValueError('Invalid _satisfies input: {}, {}'.format(value, inequality))


def _normalise_input(clause):
    ''' Reduce simple negation cases. Convert Eq to In expressions for simpler
    handling in other algorithms. '''
    if type(clause) is Eq:
        return In(clause.attribute, [clause.value])
    if type(clause) is Not:
        sub = _normalise_input(clause.clause)
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
        if type(sub) is NotIn:
            return In(sub.attribute, sub.valueset)
    return clause


def _normalise_output(clause):
    ''' For output consistency. Replace temporary NotIn objects with expression
    objects. Return In expressions with one value as Eq expresions.'''
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
    ''' Simplify Le/Lt/Ge/Gt/Eq/In expressions joined by And relation. Clauses
    are grouped by attribute and redundant expressions are eliminated or
    reduced where possible.

    Input must be an And expression. Any And/Or clauses below this level will
    not be handled (logical resolution should be applied first).

    Output guarantees:
        - No redundancy between 'simple' expressions in the top level.
        - Guaranteed false if there is a conflict between any simple
        expressions at the top level.

    A 'simple' expression is any Eq/In/Le/Lt/Ge/Gt relation, or any of those
    relations within an (arbitrarily deep) Not clause. Hence the ideal use case
    is to run this algorithm on each component of an expression in DNF form.
    '''
    assert type(expression) is And

    # Group expressions that can be simplified by attribute. Anything
    # not in scope for this algorithm is passed straight to output_clauses.
    by_attribute = collections.defaultdict(list)
    other_clauses = []
    for clause in (_normalise_input(cl) for cl in expression.clauses):
        if clause is False:
            return False
        elif clause is True:
            continue
        elif type(clause) in HANDLED_CLAUSES:
            by_attribute[clause.attribute].append(clause)
        else:
            other_clauses.append(clause)

    if len(by_attribute) == 0 and len(other_clauses) == 0:
        # All must have been True (hence skipped).
        return True

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
        if type(in_clause) is In:
            # Discrete values can be eliminated using the bounds, bound
            # expressions not required in simplified result.
            if lower_bound is not None:
                in_clause = In(attribute, [v for v in in_clause.valueset if _satisfies(v, lower_bound)])
            if upper_bound is not None:
                in_clause = In(attribute, [v for v in in_clause.valueset if _satisfies(v, upper_bound)])
            if len(in_clause.valueset) == 0:
                return False
            output_clauses.append(in_clause)
        else:
            if type(in_clause) is NotIn:
                # Values only need to be kept if they are within the range bounds.
                valueset = in_clause.valueset
                if lower_bound is not None:
                    valueset = [v for v in valueset if _satisfies(v, lower_bound)]
                if upper_bound is not None:
                    valueset = [v for v in valueset if _satisfies(v, upper_bound)]
                # If there are no values, they were all redundant and this
                # clause can be skipped (but result is not False like the 'In' case).
                if len(valueset) > 0:
                    if (
                            (lower_bound is not None and upper_bound is not None) and
                            (lower_bound.value == upper_bound.value) and
                            all(v == lower_bound.value for v in valueset)):
                        # REALLY weird special case.
                        return False
                    else:
                        output_clauses.append(NotIn(attribute, valueset))
            else:
                # 'In' case should have been handled in first branch.
                assert in_clause is None, in_clause
            # Tightest range bounds.
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
    assert not any(cl in (True, False) for cl in output_clauses)
    return And(output_clauses) if len(output_clauses) > 1 else output_clauses[0]
