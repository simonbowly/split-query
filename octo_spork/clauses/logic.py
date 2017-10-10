
import sympy as sp

from .functions import And, Or, Not


class SympyExpressionMapper(object):

    def __init__(self):
        self._mapped_values = dict()
        self._ind = 0

    def get_mapped(self, expression):
        if expression not in self._mapped_values:
            self._ind += 1
            mapped = sp.symbols('x{}'.format(self._ind))
            self._mapped_values[mapped] = expression
            self._mapped_values[expression] = mapped
        return self._mapped_values[expression]

    def get_expression(self, mapped):
        return self._mapped_values[mapped]

    def to_sympy(self, expression):
        if isinstance(expression, And):
            return sp.And(*(
                self.to_sympy(expr) for expr in expression.expressions))
        if isinstance(expression, Or):
            return sp.Or(*(
                self.to_sympy(expr) for expr in expression.expressions))
        if isinstance(expression, Not):
            return sp.Not(self.to_sympy(expression.expression))
        return self.get_mapped(expression)

    def from_sympy(self, mapped):
        if isinstance(mapped, sp.And):
            return And(self.from_sympy(expr) for expr in mapped.args)
        if isinstance(mapped, sp.Or):
            return Or(self.from_sympy(expr) for expr in mapped.args)
        if isinstance(mapped, sp.Not):
            return Not(self.from_sympy(mapped.args[0]))
        return self.get_expression(mapped)


def to_dnf(expr):
    mapper = SympyExpressionMapper()
    expr_sp = mapper.to_sympy(expr)
    expr_sp = sp.to_dnf(expr_sp, simplify=True)
    return mapper.from_sympy(expr_sp)


def to_cnf(expr):
    mapper = SympyExpressionMapper()
    expr_sp = mapper.to_sympy(expr)
    expr_sp = sp.to_cnf(expr_sp, simplify=True)
    return mapper.from_sympy(expr_sp)
