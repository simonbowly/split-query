
import pandas as pd

from split_query.expressions import Float, And, Or, Not, Eq, Le, Lt, Ge, Gt
from split_query.simplify import simplify_tree
from split_query.domain import simplify_domain
from split_query.truth_table import expand_dnf


ATTR_ERROR = "'{}' object has no attribute '{}'"


symbol_map = {
    'and': ' & ', 'or': ' | ', 'eq': '==',
    'le': '<=', 'lt': '<', 'ge': '>=', 'gt': '>',
}


def simplify(expression):
    return simplify_tree(
        simplify_domain(
            expand_dnf(
                simplify_domain(
                    simplify_tree(
                        expression)))))


def nice_repr(obj):
    if isinstance(obj, And) or isinstance(obj, Or):
        joiner = symbol_map[obj['expr']]
        return '({})'.format(joiner.join(
            nice_repr(clause) for clause in obj.clauses))
    if isinstance(obj, Not):
        return '~{}'.format(nice_repr(obj.clause))
    if any(isinstance(obj, t) for t in (Eq, Le, Lt, Ge, Gt)):
        return '({} {} {})'.format(
            nice_repr(obj.attribute), symbol_map[obj['expr']],
            nice_repr(obj.value))
    if isinstance(obj, Float):
        return nice_repr(obj.name)
    return str(obj)


class ExpressionContainer(object):
    ''' Hold an expression to allow logical operator overloading. '''

    def __init__(self, expr):
        self._wrapped = expr

    def __repr__(self):
        return 'EXPR[ {} ]'.format(repr(self._wrapped))

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

    def __repr__(self):
        return 'EXPR[ {} ]'.format(repr(self._wrapped))

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

    def __repr__(self):
        expr = simplify(self.expr)
        count = self.backend.estimate_count(expr)
        return '{}\nFilter:  {}\nRecords: {}'.format(
            self.name, nice_repr(expr), '?' if count is None else count)

    def __getattr__(self, attr):
        if attr in self.attributes:
            return AttributeContainer(self.attributes[attr])
        raise AttributeError(ATTR_ERROR.format(self.__class__.__name__, attr))

    def __getitem__(self, expr):
        return self.__class__(
            name=self.name, backend=self.backend,
            attributes=self.attributes.values(),
            expr=simplify_tree(And([self.expr, expr._wrapped])))

    def get(self):
        return self.backend.query(self.expr)


def map_query_df(df, query):
    ''' Pandas engine implementation applying a query to a dataframe.
    Returns an index on the dataframe.
    TODO implement NOT and test things. '''
    if isinstance(query, bool):
        return pd.Series(index=df.index, data=query)
    if query.expr == 'le':
        return df[query.attribute.name] <= query.value
    if query.expr == 'ge':
        return df[query.attribute.name] >= query.value
    if query.expr == 'lt':
        return df[query.attribute.name] < query.value
    if query.expr == 'gt':
        return df[query.attribute.name] > query.value
    if query.expr == 'and':
        return functools.reduce(
            lambda ind1, ind2: ind1 & ind2,
            (map_query_df(df, clause) for clause in query.clauses))
    if query.expr == 'or':
        return functools.reduce(
            lambda ind1, ind2: ind1 | ind2,
            (map_query_df(df, clause) for clause in query.clauses))


def query_df(df, query):
    ''' Use index from map_query_df to return filtered dataframe. '''
    if query is None:
        return df
    return df[map_query_df(df, query)]


class StaticDataFrameBackend(object):

    def __init__(self, df):
        self.df = df

    def query(self, expr):
        return query_df(self.df, expr)

    def estimate_count(self, expr):
        ''' Cheating here: the idea is to have a custom estimate based on the
        provided expression (e.g. from known properties of time series data). '''
        return query_df(self.df, expr).shape[0]


if __name__ == '__main__':

    import itertools
    import functools

    # Stand in for a backend function: runs queries on a grid.
    backend = StaticDataFrameBackend(pd.DataFrame(
        columns=['x', 'y'],
        data=list(itertools.product(range(10), range(10)))))

    # Interface object: filters like a dataframe.
    attributes = [Float('x'), Float('y')]
    dataset = DataSet('My dataset', attributes, backend)

    # Querying returns a new object
    filtered = dataset[dataset.x < 3][(dataset.y < 2) | (dataset.y >= 8)]
    assert dataset.expr != filtered.expr

    # get() method retrieves the actual data. This returns a dataframe which
    # can immediately be operated on. Alternative is to run get() automagically
    # when a function is called and apply the given function to the resulting
    # dataframe. But that is probably a bad idea where large remote datasets are
    # concerned.
    print(dataset)
    print()
    print(dataset.get().sum())
    print()
    print(filtered)
    print()
    print(filtered.get().sum())
    print()
    print(filtered[filtered.x > 5])
    print()
    print(filtered[filtered.x > 5].get())
