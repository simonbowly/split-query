
import collections

from octo_spork.utils import TypingMixin


class Type1(TypingMixin, collections.namedtuple('Type1', ['value1', 'value2'])):
    pass


class Type2(TypingMixin, collections.namedtuple('Type1', ['value1', 'value2'])):
    pass


def test_equals():
    ''' Identically structured objects of different types are considered unequal. '''
    assert Type1(1, 2) == Type1(1, 2)
    assert Type1(1, 2) != Type2(1, 2)
    assert Type2(1, 2) != Type1(1, 2)
    assert not Type1(1, 2) == Type2(1, 2)
    assert not Type2(1, 2) == Type1(1, 2)


def test_hashing():
    ''' Identically structured objects of different types have different hashes. '''
    assert hash(Type1(1, 2)) == hash(Type1(1, 2))
    assert hash(Type1(1, 2)) != hash(Type2(1, 2))
    assert hash(Type2(1, 2)) != hash(Type1(1, 2))
