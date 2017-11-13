
import numpy as np
import pandas as pd

from split_query.expressions import Float, And, Or, Not, Eq, Le, Lt, Ge, Gt, math_repr
from split_query.simplify import simplify_tree


ATTR_ERROR = "'{}' object has no attribute '{}'"


class ExpressionContainer(object):
    ''' Hold an expression to allow logical operator overloading. '''

    def __init__(self, expr):
        self._wrapped = expr

    def __and__(self, other):
        assert isinstance(other, ExpressionContainer)
        return ExpressionContainer(simplify_tree(And([self._wrapped, other._wrapped])))

    def __or__(self, other):
        assert isinstance(other, ExpressionContainer)
        return ExpressionContainer(simplify_tree(Or([self._wrapped, other._wrapped])))

    def __invert__(self):
        return ExpressionContainer(Not(self._wrapped))


class AttributeContainer(object):
    ''' Hold an attribute (this needs to be type specific) to allow operator
    overloading. Needs to be wrapped as __eq__ is used for comparison in the
    immutable filter expressions. Use of an operator returns a wrapped
    expression. '''

    def __init__(self, attr):
        self._wrapped = attr

    def __eq__(self, value):
        return ExpressionContainer(Eq(self._wrapped, value))

    def __le__(self, value):
        return ExpressionContainer(Le(self._wrapped, value))

    def __lt__(self, value):
        return ExpressionContainer(Lt(self._wrapped, value))

    def __ge__(self, value):
        return ExpressionContainer(Ge(self._wrapped, value))

    def __gt__(self, value):
        return ExpressionContainer(Gt(self._wrapped, value))


class DataSet(object):
    ''' Attribute access to wrapped variables, indexing access to queries.
    Any change in query returns a copied object with a new filter. Supplied
    :backend has a query method returns the result of applying the current
    :expr to the target dataset. '''

    def __init__(self, name, attributes, backend, expr=True):
        self.name = name
        self.attributes = {attr.name: attr for attr in attributes}
        self.backend = backend
        self.expr = expr

    def __getattr__(self, attr):
        if attr in self.attributes:
            return AttributeContainer(self.attributes[attr])
        raise AttributeError(ATTR_ERROR.format(self.__class__.__name__, attr))

    def __getitem__(self, expr):
        return self.__class__(
            name=self.name, backend=self.backend,
            attributes=self.attributes.values(),
            expr=simplify_tree(And([self.expr, expr._wrapped])))

    def mock_data(self):
        ''' Based on the types of attributes, return mock data. '''
        return pd.DataFrame([
            {
                name: i + j for i, name
                in enumerate(self.attributes)}
            for j in range(3)])

    def __repr__(self):
        expr = self.expr
        record_count = self.backend.estimate_count(self.expr)
        header = (
            '{}\n'.format(self.name) +
            'Filter: {}\n'.format(math_repr(self.expr)) +
            'Records: {}\n'.format(record_count) +
            'Mock data:\n')
        data = self.mock_data()
        return header + repr(data)

    def _repr_html_(self):
        expr = self.expr
        record_count = self.backend.estimate_count(self.expr)
        header = (
            '<div><H3>{}</H3></div>'.format(self.name) +
            '<br style="line-height: 0px" />' +
            '<div><b>Filter:</b> {}</div>'.format(math_repr(expr)) +
            '<div><b>Records:</b> {}</div>'.format(record_count) +
            '<br style="line-height: 0px" />' +
            '<div>Mock data:</div>')
        data = self.mock_data()
        return header + data._repr_html_()

    def get(self):
        return self.backend.query(self.expr)
