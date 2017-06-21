
class TypingMixin(object):
    ''' Mixin for classes based on namedtuples. Name of class is included
    in hashing and comparisons so that two different object types represented
    by the same tuple are considered to be unequal. '''

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return super().__eq__(other)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.__class__.__name__, super().__hash__()))
