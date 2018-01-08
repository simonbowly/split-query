''' Module for interfaces: objects which handle the user-facing part.
Currently only a pandas-type interface, where the dataset can be accessed
as if it is contained in a single dataframe. '''

from .core.expressions import And, Attribute, Eq, Ge, Gt, In, Le, Lt, Not, Or
from .core.simplify import simplify_tree


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


class DataSet(object):
    ''' DataSet object matching the pandas filtering interface. Operators
    return a new DataSet object with the same query backend and a new
    expression.

    Construction:

        dataset = DataSet(
            name='MyDataSet', attributes=['x', 'y', 'z'],
            backend=backend)

    Attribute access:

        # Returns wrapped attribute to construct filter expressions.
        dataset.x
        dataset['x']

    Filtering by indexing:

        # Returns a new DataSet with the additional filter expression Eq(x, 5).
        dataset[dataset.x > 5]

    '''

    def __init__(self, name, attributes, backend, expr=True, description=None):
        self.name = name
        self.attributes = {name: Attribute(name) for name in attributes}
        self.backend = backend
        self.expr = expr
        self.desc = description

    def __getattr__(self, attr):
        if attr in self.attributes:
            return AttributeContainer(self.attributes[attr])
        return getattr(self.backend, attr)

    def __getitem__(self, expr):
        if isinstance(expr, str) and expr in self.attributes:
            return AttributeContainer(self.attributes[expr])
        if isinstance(expr, ExpressionContainer):
            return self.__class__(
                name=self.name, backend=self.backend,
                attributes=self.attributes.values(),
                expr=simplify_tree(And([self.expr, expr.wrapped])),
                description=self.desc)
        raise KeyError(repr(expr))

    def __dir__(self):
        return list(self.attributes.keys()) + ['get']

    def _repr_html_(self):
        header = (
            '<div><H3>{}</H3></div>'.format(self.name) +
            ('' if self.desc is None else '<div>{}</div>'.format(self.desc)) +
            '<br style="line-height: 0px" />' +
            '<div><b>Filter:</b> {}</div>'.format(repr(self.expr)) +
            '<div><b>Records:</b> {}</div>'.format(-1) +
            '<br style="line-height: 0px" />' +
            '<div>Mock data:</div>')
        return header
        # data = self.backend.mock_data()
        # return header + data._repr_html_()

    def get(self):
        return self.backend.get(self.expr)
