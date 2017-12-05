''' Tests of the pandas-like interface object, functioning as API guarantees. '''

import itertools
from unittest import mock

import pytest

from split_query.interface import DataSet
from split_query.core.expressions import (And, Attribute, Eq, Ge, Gt, In, Le, Lt,
                                     Not, Or)


def filter_test(test_func):
    ''' Decorates a test function to supply it with a clean DataSet object,
    inject mock backend and assert query result. The decorated function should
    return the new dataset object created by the filter, and the expected
    expression to be passed to the backend. The tests then simply expression
    the relationship betwen the API and the resulting query expression. '''
    def _func():
        backend = mock.Mock()
        dataset = DataSet('Data', list('xyzs'), backend)
        # Filtered is a new DataSet. get() executes the query on the backend.
        filtered, expression = test_func(dataset)
        result = filtered.get()
        # Check query received correct expression, result is query output.
        backend.get.assert_called_once_with(expression)
        assert result == backend.get()
        # Check that the original dataset object was not changed.
        backend.reset_mock()
        result = dataset.get()
        backend.get.assert_called_once_with(True)
        assert result == backend.get()
    return _func


@filter_test
def test_no_filter(dataset):
    return (
        dataset,
        True)


@filter_test
def test_filter_eq(dataset):
    return (
        dataset[dataset.x == 4],
        Eq(Attribute('x'), 4))


@filter_test
def test_filter_eq_getitem(dataset):
    return (
        dataset[dataset['x'] == 4],
        Eq(Attribute('x'), 4))


@filter_test
def test_filter_chained(dataset):
    return (
        dataset[dataset.x <= 1][dataset.z >= 0],
        And([Le(Attribute('x'), 1), Ge(Attribute('z'), 0)]))


@filter_test
def test_filter_and(dataset):
    return (
        dataset[(dataset.y < 2) & (dataset.x > 5)],
        And([Lt(Attribute('y'), 2), Gt(Attribute('x'), 5)]))


@filter_test
def test_filter_or(dataset):
    return (
        dataset[(dataset.y == 2) | (dataset.z < 1)],
        Or([(Eq(Attribute('y'), 2)), Lt(Attribute('z'), 1)]))


@filter_test
def test_filter_not(dataset):
    return (
        dataset[~(dataset.y <= 2)],
        Not(Le(Attribute('y'), 2)))


@filter_test
def test_filter_isin(dataset):
    return (
        dataset[dataset.s.isin(['a', 'b', 'c'])],
        In(Attribute('s'), ['a', 'b', 'c']))


@filter_test
def test_filter_between(dataset):
    return (
        dataset[dataset.x.between(1, 3)],
        And([Ge(Attribute('x'), 1), Le(Attribute('x'), 3)]))
