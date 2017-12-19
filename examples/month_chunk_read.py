
import itertools
from datetime import datetime

import pandas as pd

from split_query.core import (And, Attribute, Eq, In, Le, Lt, Ge, Gt,
                              simplify_domain, traverse_expression)


def read_chunks_grouped(file_name, grouper, **read_kwargs):
    ''' Break up reading large file by month. Requires ordered data. '''
    for chunk in pd.read_csv(file_name, **read_kwargs):
        for group in sorted(chunk.groupby(grouper)):
            yield group


def read_by_group(file_name, grouper, **read_kwargs):
    ''' Read file in chunks, returning a generator of groups produced by
    grouper. Returns the equivalent of
    read_csv(file_name).groupby(grouper).groups, but requires that the groups
    appear in order (for memory reasons). '''
    current_month, current_df = None, None
    for month, df in read_chunks_grouped(file_name, grouper, **read_kwargs):
        if current_month is None:
            current_month, current_df = month, [df]
        else:
            assert month >= current_month
            if month == current_month:
                current_df.append(df)
            else:
                yield current_month, pd.concat(current_df)
                current_month, current_df = month, [df]
    yield current_month, pd.concat(current_df)


def map_parts(iterable):
    for (year, month), df in iterable:
        df['date'] = pd.to_datetime(df[['Year', 'Month', 'DayofMonth']].rename(
            columns={'DayofMonth': 'Day'}))
        start = datetime(year, month, 1)
        end = (start + pd.tseries.offsets.MonthBegin()).to_pydatetime()
        expression = And([
            Ge(Attribute('date'), start), Lt(Attribute('date'), end)])
        yield expression, df


def get_years(years):
    return map_parts(itertools.chain(*(
        read_by_group(
            '/home/simon/Downloads/airline_data/{}.csv.bz2'.format(year),
            grouper=['Year', 'Month'], compression='bz2', chunksize=100000)
        for year in years)))


def _filter_year_only(obj):
    if any(isinstance(obj, cls) for cls in [Eq, In, Le, Lt, Ge, Gt]):
        if obj.attribute == Attribute('date'):
            if isinstance(obj, Gt) or isinstance(obj, Ge):
                return Ge(Attribute('year'), obj.value.year)
            if isinstance(obj, Lt) or isinstance(obj, Le):
                return Le(Attribute('year'), obj.value.year)
            return obj
        else:
            return True
    return obj


def expr_to_years(expression):
    year_expr = simplify_domain(traverse_expression(
        expression, hook=_filter_year_only))
    _intersections = (
        simplify_domain(And([year_expr, Eq(Attribute('year'), year)]))
        for year in range(1987, 2009))
    return [int(obj.value) for obj in _intersections if obj is not False]


def get(expression):
    ''' Returns the required superset query in parts iterator. '''
    return get_years(expr_to_years(expression))


if __name__ == '__main__':
    expression = And([
        Ge(Attribute('date'), datetime(1987, 11, 1)),
        Lt(Attribute('date'), datetime(1989, 2, 1))])
    for query, df in get(expression):
        print(query, df.shape)
