
import json, timeit
from tqdm import tqdm
import pandas as pd
from split_query.core import object_hook, And, Not
from split_query.core.expand import expand_dnf_simplify, get_clauses


with open('path_inmemory.json') as infile:
    path_inmemory = json.load(infile, object_hook=object_hook)
with open('path_persistent.json') as infile:
    path_persistent = json.load(infile, object_hook=object_hook)


def bench(path, name):
    for i, (_, current, cached) in enumerate(path):
        intersection = And([current, cached])
        difference = And([current, Not(cached)])
        def run_intersection():
            expand_dnf_simplify(intersection)
        def run_difference():
            expand_dnf_simplify(difference)
        yield dict(
            name=name, ind=i, clauses=len(get_clauses(intersection)),
            intersection=min(timeit.repeat(run_intersection, number=1, repeat=1)),
            difference=min(timeit.repeat(run_difference, number=1, repeat=1)))

results = (
    list(bench(tqdm(path_inmemory, maxinterval=1), 'in-memory')) +
    list(bench(tqdm(path_persistent, maxinterval=1), 'persistent')))

pd.DataFrame(results).to_csv('benchmarks.csv', index=False)
