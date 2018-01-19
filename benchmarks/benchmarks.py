
import timeit
import random
from datetime import datetime, timedelta

import pandas as pd
from tqdm import trange, tqdm

from split_query.core import And, Or, Not, Eq, Le, Lt, Ge, Gt, In, Attribute
from split_query.core.expand import expand_dnf_simplify as simplify

################ FUNCTIONS TO BENCHMARK ################

def intersects(expr1, expr2):
    ''' Return whether e1 intersects with e2. '''
    expression = And([expr1, expr2])
    expression = simplify(expression)
    return expression is not False

def intersection(expr1, expr2):
    expression = And([expr1, expr2])
    expression = simplify(expression)
    return expression

def remains(expr1, expr2):
    expression = And([expr1, Not(expr2)])
    expression = simplify(expression)
    return expression is not False

def remainder(expr1, expr2):
    expression = And([expr1, Not(expr2)])
    expression = simplify(expression)
    return expression

################# INPUT GENERATOR ######################

def generate_block(*args, overlap):
    ''' Generate pairs, where the overlap in {'partial', 'none', 'superset'}. '''
    clauses1 = []
    clauses2 = []
    for i, arg in enumerate(args):
        attr = Attribute('x{}'.format(i))
        if arg == 'dt' or arg == 'num':
            start_dt = random.randint(2100, 3000)
            end_dt = start_dt + 1000
            start_shift = (
                random.randint(200, 500) if overlap == 'partial'
                else random.randint(2000, 2500) if overlap == 'none'
                else random.randint(-500, -200) if overlap == 'superset' else None)
            end_shift = (
                random.randint(200, 500) if overlap == 'partial' or overlap == 'superset'
                else random.randint(2000, 2500) if overlap == 'none' else None)
            if arg == 'num':
                clauses1.extend([Ge(attr, start_dt), Le(attr, end_dt)])
                clauses2.extend([
                    Ge(attr, start_dt + start_shift),
                    Le(attr, end_dt + end_shift)])
            else:
                clauses1.extend([
                    Ge(attr, datetime.fromordinal(start_dt)),
                    Le(attr, datetime.fromordinal(end_dt))])
                clauses2.extend([
                    Ge(attr, datetime.fromordinal(start_dt + start_shift)),
                    Le(attr, datetime.fromordinal(end_dt + end_shift))])
        elif arg == 'arg':
            valueset = [random.randint(0, 10) for _ in range(4)]
            clauses1.append(In(attr, valueset))
            clauses2.append(In(attr, (
                valueset[:2] + [random.randint(20, 30) for _ in range(2)] if overlap == 'partial'
                else [random.randint(20, 30) for _ in range(4)] if overlap == 'none'
                else valueset + [random.randint(20, 30) for _ in range(2)] if overlap == 'superset'
                else None)))
        else:
            raise ValueError(arg)

    return And(clauses1), And(clauses2)

################## SAMPLING ######################

def sample(*args, overlap, number=10):
    expr1, expr2 = generate_block(*args, overlap=overlap)
    def t_int():
        intersects(expr1, expr2)
    def t_rem():
        remains(expr1, expr2)
    return {
        'overlap': overlap,
        'cat': '-'.join(args),
        'intersects': intersects(expr1, expr2),
        'remains': remains(expr1, expr2),
        'intersects_time': min(timeit.repeat(t_int, number=number, repeat=3)) / number,
        'remains_time': min(timeit.repeat(t_rem, number=number, repeat=3)) / number}


if __name__ == '__main__':
    result = pd.DataFrame([
        sample(*args, overlap=overlap) for args in tqdm([
            ('dt',), ('num',), ('arg',),
            ('dt', 'num'), ('dt', 'arg'), ('num', 'arg'),
            ], leave=False)
        for overlap in tqdm(['partial', 'none', 'superset'], leave=False)
        for _ in trange(10, leave=False)])
    result.to_csv('benchmark_results.csv', header=True, index=False)
    print(result.groupby(['cat', 'overlap']).mean().sort_values('intersects_time'))
