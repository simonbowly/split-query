''' Library of immutable objects used to describe the content of a query. '''

import frozendict


class Expression(frozendict.frozendict):
    ''' Borrows the data structures from a frozendict to create immutable
    objects. Child class constructor should give a unique name to ensure it
    is indistinguishable from other frozendicts. Resulting objects have a
    dictionary representation, making it easier to serialise, compare and hash.
    '''

    def __init__(self, expr, **kwargs):
        super().__init__(kwargs, expr=expr)

    def __getattr__(self, attr):
        ''' Attribute read access to the dict key-values for convenience. '''
        if attr in self:
            return self[attr]
        raise AttributeError("'{}' object has no attribute '{}'".format(
            self.__class__.__name__, attr))


class Attribute(Expression):
    ''' Named continuous numerical attribute. '''

    def __init__(self, name):
        super().__init__('attr', name=name)

    def __repr__(self):
        return self.name


class BinaryRelation(Expression):
    ''' Injects a named-class repr for attr-value relations. '''

    def __repr__(self):
        return '{}({},{})'.format(
            self.__class__.__name__,
            repr(self.attribute), repr(self.value))


class Eq(BinaryRelation):
    ''' Binary expression: attribute == value. '''

    def __init__(self, attribute, value):
        super().__init__('eq', attribute=attribute, value=value)


class Le(BinaryRelation):
    ''' Binary expression: attribute <= value. '''

    def __init__(self, attribute, value):
        super().__init__('le', attribute=attribute, value=value)


class Lt(BinaryRelation):
    ''' Binary expression: attribute < value. '''

    def __init__(self, attribute, value):
        super().__init__('lt', attribute=attribute, value=value)


class Ge(BinaryRelation):
    ''' Binary expression: attribute >= value. '''

    def __init__(self, attribute, value):
        super().__init__('ge', attribute=attribute, value=value)


class Gt(BinaryRelation):
    ''' Binary expression: attribute > value. '''

    def __init__(self, attribute, value):
        super().__init__('gt', attribute=attribute, value=value)


class In(Expression):

    def __init__(self, attribute, valueset):
        super().__init__(
            'in', attribute=attribute, valueset=frozenset(valueset))

    def __repr__(self):
        return 'In({},{})'.format(
            repr(self.attribute), repr(sorted(self.valueset)))


class LogicalRelation(Expression):
    ''' Injects a named-class repr method for And/Or. '''

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(list(self.clauses)))


class And(LogicalRelation):
    ''' Logical expression linking clauses with AND. '''

    def __init__(self, clauses):
        super().__init__('and', clauses=frozenset(clauses))


class Or(LogicalRelation):
    ''' Logical expression linking clauses with OR. '''

    def __init__(self, clauses):
        super().__init__('or', clauses=frozenset(clauses))


class Not(Expression):
    ''' Logical expression negating a clause. '''

    def __init__(self, clause):
        super().__init__('not', clause=clause)

    def __repr__(self):
        return 'Not({})'.format(repr(self.clause))


symbol_map = {
    'and': ' & ', 'or': ' | ', 'eq': '==',
    'le': '<=', 'lt': '<', 'ge': '>=', 'gt': '>',
}


def math_repr(obj):
    if isinstance(obj, And) or isinstance(obj, Or):
        joiner = symbol_map[obj['expr']]
        return joiner.join(sorted(
            '({})'.format(math_repr(clause)) for clause in obj.clauses))
    if isinstance(obj, Not):
        return '~({})'.format(math_repr(obj.clause))
    if any(isinstance(obj, t) for t in (Eq, Le, Lt, Ge, Gt)):
        return '{} {} {}'.format(
            math_repr(obj.attribute), symbol_map[obj['expr']],
            math_repr(obj.value))
    if isinstance(obj, Attribute):
        return math_repr(obj.name)
    if isinstance(obj, In):
        return '{} in {}'.format(
            repr(obj.attribute), repr(sorted(obj.valueset)))
    return str(obj)
