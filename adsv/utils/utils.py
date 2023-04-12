import inspect
import os
from collections.abc import Iterator


def Or(*args):
    for arg in args:
        if isinstance(arg, Iterator):
            if Or(*arg): return True
        else:
            if arg: return True
    return False


def And(*args):
    for arg in args:
        if isinstance(arg, Iterator):
            if not And(*arg): return False
        else:
            if not arg: return False
    return True


class Counter:
    def __init__(self, start=0):
        self._count = start

    def get(self):
        self._count += 1
        return self._count - 1
