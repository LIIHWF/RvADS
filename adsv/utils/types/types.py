from typing import Union, Iterator, Iterable, Optional, Callable, Tuple, Dict, Set, Any, TypeVar, Sequence, Generic
from multimethod import multimeta
from google.protobuf.message import Message
from abc import abstractmethod
Number = Union[int, float]


T = TypeVar('T')


def overload(func):
    return func


INF = float('inf')


class ProtoClass:
    @abstractmethod
    def __init__(self, proto: 'Message'):
        raise NotImplementedError

    @abstractmethod
    def dump(self) -> 'Message':
        raise NotImplementedError


T = TypeVar('T')

IterableSequence = Union[Sequence[T], Iterable[T]]
