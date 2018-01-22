'''
Profiling a large-ish DNF expansion, shows a couple of things:
    - A few operations on boolean logic can be short-circuited
    - There is a lot of hashing done, for example any creation of an And/Or
    adds expressions to a set, relations are stored in a dict to calculate
    the truth table. Both structures are hash table backed, but the first is
    likely unnecessary and the second usually has very small tables. Hashing
    seems to be faster than comparison, so the structure is probably still
    the correct one; just need to minimise the number of lookups.
python -m cProfile -o profile.out testcase.py && cprofilev -f profile.out
'''

import json
from split_query.core import object_hook, And, Not
from split_query.core.expand import expand_dnf_simplify

with open('path_persistent.json') as infile:
    _, e1, e2 = json.load(infile, object_hook=object_hook)[3]

expand_dnf_simplify(And([e1, Not(e2)]))
