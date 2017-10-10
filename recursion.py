
from octo_spork.clauses import And, Or, Not, In, simplify

expr = And([
    And([In('col1', [1, 2, 3]), In('col2', [4, 5, 6, 7])]),
    Not(And([In('col1', [2]), In('col2', [4, 5, 6])]))])

# expr = Or([Not(In('col2', [4, 5, 6])), Not(In('col1', [2]))])

res = simplify(expr)

print()
print()
print(expr)
print(res)
