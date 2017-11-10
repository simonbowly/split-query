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


class Float(Expression):
    ''' Named continuous numerical attribute. '''

    def __init__(self, name):
        super().__init__('attr', dtype='float', name=name)

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
