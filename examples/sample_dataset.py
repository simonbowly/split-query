
import itertools
import logging

import pandas as pd
import numpy as np

from split_query.core import simplify_domain, expand_dnf, And, Or, Ge, Le, Gt, Lt, In, Attribute
from split_query.decorators import dataset, cache_persistent
from split_query.remote import with_only_fields


def remote_query(start_time, end_time, tag_name, interval):
    ''' Return a dataframe which is the result of querying the remote dataset
    for all records with the given parameters. Since the cache filters based
    on the data, make sure the columns timestamp, tag_name and interval are
    present in the returned dataframes. '''
    logging.info('REMOTE {}[{}]: {} -> {}'.format(
         tag_name, interval, start_time.isoformat(), end_time.isoformat()))
    date_range = pd.date_range(start_time, end_time, freq=interval, name='timestamp')
    df = pd.DataFrame(index=date_range, data=dict(
        tag_name=[tag_name] * date_range.shape[0],
        interval=[interval] * date_range.shape[0],
        value=np.random.random(date_range.shape[0]))).reset_index()
    logging.info('REMOTE {} records'.format(df.shape[0]))
    return df


@dataset(name='SampleDataset', attributes=['timestamp', 'tag_name', 'interval', 'value'])
@cache_persistent('sample_data')   # Use this instead for persistent file cache.
class SampleDataset(object):
    ''' This docstring will be displayed in the dataset object repr. '''

    def get(self, expression):
        ''' Wrapper function for remote_query to handle the expressions language input
        and expected output for cache. '''

        # Simplify the query to only the fields that are filtered by the remote.
        expression = with_only_fields(expression, attributes=['timestamp', 'tag_name', 'interval'])

        # Break query into subqueries fitting the remote function.
        expanded = simplify_domain(expand_dnf(expression))
        if isinstance(expanded, And):
            subqueries = [expanded]
        elif isinstance(expanded, Or):
            subqueries = list(expanded.clauses)
        else:
            raise ValueError('Expression may be too broad.')

        # Extract args and call remote for each subquery. If the input expression filters
        # properly on all required fields, then the DNF expansion should give something like:
        #   timestamp >= start_time & timestamp <= end_time &
        #   interval in [intervals] & tag_name in [tag_names]

        for subquery in subqueries:

            # Find Ge/Gt and Le/Lt expressions indicating the timestamp range.
            time_range = with_only_fields(subquery, ['timestamp'])
            assert isinstance(time_range, And) and len(time_range.clauses) == 2
            time_range = sorted(time_range.clauses, key=lambda obj: obj.__class__.__name__)
            assert isinstance(time_range[0], Ge) or isinstance(time_range[0], Gt)
            assert isinstance(time_range[1], Le) or isinstance(time_range[1], Le)
            start_time = time_range[0].value
            end_time = time_range[1].value

            # Find In expressions for each of the tag-like fields.
            tag_names = with_only_fields(subquery, ['tag_name'])
            assert isinstance(tag_names, In)
            intervals = with_only_fields(subquery, ['interval'])
            assert isinstance(intervals, In)

            # Run a separate remote query over this date range for each tag and interval.
            # Apart from making the remote_query function simpler (deals with exactly one
            # tag, one interval and start/end time), it also means the cache stores data
            # in smaller chunks which should be faster to retrieve, with less memory overhead.
            for tag_name, interval in itertools.product(tag_names.valueset, intervals.valueset):
                actual_subquery = And([
                    Ge(Attribute('timestamp'), start_time),
                    Le(Attribute('timestamp'), end_time),
                    In(Attribute('tag_name'), [tag_name]),
                    In(Attribute('interval'), [interval])])
                yield actual_subquery, remote_query(start_time, end_time, tag_name, interval)
