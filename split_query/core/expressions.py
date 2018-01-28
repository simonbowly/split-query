''' Library of immutable objects used to describe the content of a query. '''

from builtins import super


class Expression(object):
    ''' Base class for all expression objects. '''
    pass


class Attribute(Expression):
    ''' Class representing a named attribute in a dataset. '''

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'ATTR({})'.format(self.name)

    def __eq__(self, other):
        return isinstance(other, Attribute) and (self.name == other.name)

    def __hash__(self):
        return hash(self.name)


class ConditionalRelation(Expression):
    ''' Class representing a condition on values in the data. '''

    def __init__(self, attribute, value):
        self.attribute = attribute
        self.value = value

    def __repr__(self):
        return '{}({},{})'.format(
            self.__class__.__name__,
            repr(self.attribute), repr(self.value))

    def __eq__(self, other):
        return (
            (type(self) == type(other)) and
            (self.attribute == other.attribute) and
            (self.value == other.value))

    def __hash__(self):
        return hash((self.__class__.__name__, self.attribute, self.value))


class Eq(ConditionalRelation):
    ''' Binary expression: attribute == value. '''
    pass


class Le(ConditionalRelation):
    ''' Binary expression: attribute <= value. '''
    pass


class Lt(ConditionalRelation):
    ''' Binary expression: attribute < value. '''
    pass


class Ge(ConditionalRelation):
    ''' Binary expression: attribute >= value. '''
    pass


class Gt(ConditionalRelation):
    ''' Binary expression: attribute > value. '''
    pass


class In(ConditionalRelation):
    ''' Binary expression: attribute is in [values]. '''

    def __init__(self, attribute, valueset):
        super().__init__(attribute, tuple(valueset))

    @property
    def valueset(self):
        return self.value


class LogicalRelation(Expression):
    ''' Class representing logical And/Or/Not compositions. '''
    pass


class And(LogicalRelation):
    ''' Logical expression linking clauses with AND. '''

    def __init__(self, clauses):
        self.clauses = tuple(clauses)

    def __repr__(self):
        return 'AND({})'.format(repr(self.clauses))

    def __eq__(self, other):
        return isinstance(other, And) and (self.clauses == other.clauses)

    def __hash__(self):
        return hash(('and', self.clauses))


class Or(LogicalRelation):
    ''' Logical expression linking clauses with OR. '''

    def __init__(self, clauses):
        self.clauses = tuple(clauses)

    def __repr__(self):
        return 'OR({})'.format(repr(self.clauses))

    def __eq__(self, other):
        return isinstance(other, Or) and (self.clauses == other.clauses)

    def __hash__(self):
        return hash(('or', self.clauses))


class Not(LogicalRelation):
    ''' Logical expression negating a clause. '''

    def __init__(self, clause):
        self.clause = clause

    def __repr__(self):
        return 'Not({})'.format(repr(self.clause))

    def __eq__(self, other):
        return isinstance(other, Not) and (self.clause == other.clause)

    def __hash__(self):
        return hash(('not', self.clause))
