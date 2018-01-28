
from .expressions import And, Attribute, Eq, Ge, Gt, In, Le, Lt, Not, Or
from .logic import simplify_tree


class AttributeContainer(object):
    ''' Wraps an attribute (not type specific) to allow operator overloading.
    Attributes need to be wrapped as __eq__ is used for comparison of the
    immutable attribute objects. All methods return wrapped expressions.

    Handles these operators:

        attr == value  ->  Eq(attr, value)
        attr <= value  ->  Le(attr, value)
        attr < value   ->  Lt(attr, value)
        attr >= value  ->  Ge(attr, value)
        attr > value   ->  Gt(attr, value)

        attr.isin([v1, v2, ...])  ->  In(attr, [v1, v2, ...])
        attr.between(a, b)        ->  And([Ge(attr, a), Le(attr, b)])

    '''

    def __init__(self, attr):
        self.wrapped = attr

    def __eq__(self, value):
        return ExpressionContainer(Eq(self.wrapped, value))

    def __le__(self, value):
        return ExpressionContainer(Le(self.wrapped, value))

    def __lt__(self, value):
        return ExpressionContainer(Lt(self.wrapped, value))

    def __ge__(self, value):
        return ExpressionContainer(Ge(self.wrapped, value))

    def __gt__(self, value):
        return ExpressionContainer(Gt(self.wrapped, value))

    def isin(self, valueset):
        return ExpressionContainer(In(self.wrapped, valueset))

    def between(self, lower, upper):
        return ExpressionContainer(
            And([Ge(self.wrapped, lower), Le(self.wrapped, upper)]))


class ExpressionContainer(object):
    ''' Wraps an expression to allow logical operator overloading. All methods
    required wrapped expressions as inputs and return new wrapped expressions.
    Applies simplify_tree for And and Or expressions to flatten trees.

    Handles these operators:

        e1 & e2  ->  And([e1, e2])
        e1 | e2  ->  Or([e1, e2])
        ~e1      ->  Not(e1)

    '''

    def __init__(self, expr):
        self.wrapped = expr

    def __and__(self, other):
        assert isinstance(other, ExpressionContainer)
        return ExpressionContainer(simplify_tree(And([self.wrapped, other.wrapped])))

    def __or__(self, other):
        assert isinstance(other, ExpressionContainer)
        return ExpressionContainer(simplify_tree(Or([self.wrapped, other.wrapped])))

    def __invert__(self):
        return ExpressionContainer(Not(self.wrapped))


def attribute(name):
    return AttributeContainer(Attribute(name))


def expression(container):
    return container.wrapped
