''' Module for interfaces: objects which handle the user-facing part.
Currently only a pandas-type interface, where the dataset can be accessed
as if it is contained in a single dataframe. '''

from .core.expressions import Attribute, And
from .core.logic import simplify_tree
from .core.wrappers import AttributeContainer, ExpressionContainer


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
