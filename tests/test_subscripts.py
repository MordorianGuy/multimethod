import sys
import pytest
from typing import Callable, Generic, List, Sequence, TypeVar
from multimethod import multimethod, subtype, DispatchError


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Literal added in 3.8")
def test_literals():
    from typing import Literal

    assert issubclass(subtype(Literal['a', 'b']), str)
    assert not issubclass(subtype(Literal['a']), subtype(List[int]))
    tp = subtype(Literal['a', 0])
    assert issubclass(tp.get_type('a'), tp)
    assert issubclass(tp.get_type(0), tp)
    assert not issubclass(tp.get_type('b'), tp)
    assert tp.get_type('b') is str
    assert tp.get_type(0.0) is float

    @multimethod
    def func(arg: Literal['a', 0]):
        return arg

    assert func(0) == 0
    with pytest.raises(DispatchError):
        assert func(1)
    with pytest.raises(DispatchError):
        func(0.0)


def test_generic():
    class cls(Generic[TypeVar('T')]):
        pass

    @multimethod
    def func(x: cls[int]):
        pass

    assert func(cls[int]()) is None


def test_empty():
    @multimethod
    def func(arg: List[int]):
        return int

    @func.register
    def _(arg: List[bool]):
        return bool

    assert func([0]) is int
    assert func([False]) is func([]) is bool


def test_callable():
    def f(arg: bool) -> int:
        ...

    def g(arg: int) -> bool:
        ...

    def h(arg) -> bool:
        ...

    @multimethod
    def func(arg: Callable[[bool], bool]):
        return arg.__name__

    @func.register
    def _(arg: Callable[..., bool]):
        return ...

    @func.register
    def _(arg: int):
        return 'int'

    @func.register
    def _(arg: Sequence[Callable[[bool], bool]]):
        return arg[0].__name__ + "0"

    tp = subtype(func.__annotations__['arg'])
    assert not issubclass(tp.get_type(f), tp.get_type(g))
    assert issubclass(tp.get_type(g), tp.get_type(f))
    with pytest.raises(DispatchError):
        func(f)
    assert func(g) == 'g'
    assert func([g]) == 'g0'
    assert func(h) is ...