
import frozendict


class ExpressionBase(frozendict.frozendict):
    ''' Borrows the data structures from a frozendict to create immutable
    objects. Child class constructor should give a unique name to ensure it
    is indistinguishable from other frozendicts. Resulting objects have a
    dictionary representation, making it easier to serialise, compare and hash.
    '''

    def __init__(self, expr, **kwargs):
        super().__init__(kwargs, expr=expr)

    def __getattr__(self, attr):
        ''' Attribute read access to the dict key-values for convenience. '''
        if attr in self:
            return self[attr]
        raise AttributeError("'{}' object has no attribute '{}'".format(
            self.__class__.__name__, attr))


class Attribute(ExpressionBase):
    ''' A named attribute of the objects being filtered. '''

    def __init__(self, name):
        super().__init__('attr', name=name)


class Eq(ExpressionBase):
    ''' Binary expression: attribute == value. '''

    def __init__(self, attribute, value):
        super().__init__('eq', attribute=attribute, value=value)


class Le(ExpressionBase):
    ''' Binary expression: attribute <= value. '''

    def __init__(self, attribute, value):
        super().__init__('le', attribute=attribute, value=value)


class Lt(ExpressionBase):
    ''' Binary expression: attribute < value. '''

    def __init__(self, attribute, value):
        super().__init__('lt', attribute=attribute, value=value)


class Ge(ExpressionBase):
    ''' Binary expression: attribute >= value. '''

    def __init__(self, attribute, value):
        super().__init__('ge', attribute=attribute, value=value)


class Gt(ExpressionBase):
    ''' Binary expression: attribute > value. '''

    def __init__(self, attribute, value):
        super().__init__('gt', attribute=attribute, value=value)


class In(ExpressionBase):
    ''' Binary expression: attribute takes on value from set. '''

    def __init__(self, attribute, valueset):
        super().__init__(
            'in', attribute=attribute, valueset=frozenset(valueset))


class And(ExpressionBase):
    ''' Logical expression linking clauses with AND. '''

    def __init__(self, clauses):
        super().__init__('and', clauses=frozenset(clauses))


class Or(ExpressionBase):
    ''' Logical expression linking clauses with OR. '''

    def __init__(self, clauses):
        super().__init__('or', clauses=frozenset(clauses))


class Not(ExpressionBase):
    ''' Logical expression negating a clause. '''

    def __init__(self, clause):
        super().__init__('not', clause=clause)


symbol_map = {
    'and': ' & ', 'or': ' | ', 'eq': '==',
    'le': '<=', 'lt': '<', 'ge': '>=', 'gt': '>',
}


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
    if isinstance(obj, Attribute):
        return nice_repr(obj.name)
    return str(obj)
