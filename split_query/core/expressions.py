''' Library of immutable objects used to describe the content of a query. '''

from builtins import super


class Expression(object):
    pass


class Attribute(Expression):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'ATTR({})'.format(self.name)

    def __eq__(self, other):
        return isinstance(other, Attribute) and (self.name == other.name)

    def __hash__(self):
        return hash(self.name)


class AttributeRelation(Expression):

    def __init__(self, attribute, value):
        self.attribute = attribute
        self.value = value

    def __repr__(self):
        return '{}({},{})'.format(
            self.__class__.__name__,
            repr(self.attribute), repr(self.value))

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            (self.attribute == other.attribute) and
            (self.value == other.value))

    def __hash__(self):
        return hash((self.__class__.__name__, self.attribute, self.value))

    @property
    def expr(self):
        return self.__class__.__name__.lower()


class Eq(AttributeRelation):
    ''' Binary expression: attribute == value. '''
    pass


class Le(AttributeRelation):
    ''' Binary expression: attribute <= value. '''
    pass


class Lt(AttributeRelation):
    ''' Binary expression: attribute < value. '''
    pass


class Ge(AttributeRelation):
    ''' Binary expression: attribute >= value. '''
    pass


class Gt(AttributeRelation):
    ''' Binary expression: attribute > value. '''
    pass


class In(AttributeRelation):
    ''' Binary expression: attribute is in value. '''

    def __init__(self, attribute, valueset):
        super().__init__(attribute, frozenset(valueset))

    @property
    def valueset(self):
        return self.value


class LogicalRelation(Expression):
    ''' Injects a named-class repr method for And/Or. '''
    pass


class And(LogicalRelation):
    ''' Logical expression linking clauses with AND. '''

    def __init__(self, clauses):
        self.clauses = frozenset(clauses)

    def __repr__(self):
        return 'AND({})'.format(repr(list(self.clauses)))

    def __eq__(self, other):
        return isinstance(other, And) and (self.clauses == other.clauses)

    def __hash__(self):
        return hash(('and', self.clauses))


class Or(LogicalRelation):
    ''' Logical expression linking clauses with OR. '''

    def __init__(self, clauses):
        self.clauses = frozenset(clauses)

    def __repr__(self):
        return 'OR({})'.format(repr(list(self.clauses)))

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
