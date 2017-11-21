
import itertools
from unittest import mock

import pytest

from interface import DataSet
from split_query.expressions import (And, Attribute, Eq, Ge, Gt, In, Le, Lt,
                                     Not, Or)


def filter_test(test_func):
    ''' Decorates a test function to supply it with a clean DataSet object,
    inject mock backend and assert query result. The decorated function should
    return the new dataset object created by the filter, and the expected
    expression. This approach allows the tests to simply express the
    relationship between the API and the query call. '''
    def _func():
        backend = mock.Mock()
        attributes = [Attribute(n) for n in 'xyz'] + [Attribute('s')]
        dataset = DataSet('Data', attributes, backend)
        # Filtered is a new DataSet. get() executes the query on the backend.
        filtered, expression = test_func(dataset)
        result = filtered.get()
        # Check query received correct expression, result is query output.
        backend.query.assert_called_once_with(expression)
        assert result == backend.query()
        # Check that the original dataset object was not changed.
        backend.reset_mock()
        result = dataset.get()
        backend.query.assert_called_once_with(True)
        assert result == backend.query()
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


@mock.patch('interface.math_repr', return_value='math')
def test_dataset_repr(math_repr):
    # Backend only used for a record count estimate.
    backend = mock.Mock()
    backend.estimate_count.return_value = 15

    attributes = [Attribute(n) for n in 'xyz']
    dataset = DataSet('Data', attributes, backend)
    dataset = dataset[dataset.x == 0]
    # Takes the place of a returned dataframe. It will simply have its
    # repr called to add to the end of the output string.
    dataset.mock_data = mock.Mock(return_value='MOCK_DF')

    result = repr(dataset)
    math_repr.assert_called_once_with(Eq(Attribute('x'), 0))
    backend.estimate_count.assert_called_once_with(Eq(Attribute('x'), 0))
    assert result == "Data\nFilter: math\nRecords: 15\nMock data:\n'MOCK_DF'"


@mock.patch('interface.math_repr', return_value='mathy')
def test_dataset_repr_html(math_repr):
    # Backend only used for a record count estimate.
    backend = mock.Mock()
    backend.estimate_count.return_value = 12

    attributes = [Attribute(n) for n in 'xyz']
    dataset = DataSet('OtherData', attributes, backend)
    dataset = dataset[dataset.y == 1]
    # Takes the place of a returned dataframe. It will simply have its
    # repr called to add to the end of the output string.
    dataset.mock_data = mock.Mock()
    dataset.mock_data()._repr_html_.return_value = 'mock_repr'

    result = dataset._repr_html_()
    math_repr.assert_called_once_with(Eq(Attribute('y'), 1))
    backend.estimate_count.assert_called_once_with(Eq(Attribute('y'), 1))
    assert result == (
        '<div><H3>OtherData</H3></div>' +
        '<br style="line-height: 0px" />' +
        '<div><b>Filter:</b> mathy</div>' +
        '<div><b>Records:</b> 12</div>' +
        '<br style="line-height: 0px" />' +
        '<div>Mock data:</div>mock_repr')


def test_mock_data():
    attributes = [Attribute(n) for n in 'xyz']
    dataset = DataSet('OtherData', attributes, None)
    mock_data = dataset.mock_data()
    assert mock_data.to_dict() == dict(
        x={0:0, 1:1, 2:2},
        y={0:1, 1:2, 2:3},
        z={0:2, 1:3, 2:4})
