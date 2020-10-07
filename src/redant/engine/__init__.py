#!/usr/bin/env python

from abc import ABCMeta, abstractproperty, abstractmethod

class EngineBase(object, metaclass=ABCMeta):
    #
    __metaclass__ = ABCMeta
    #
    #
    def __new__(cls, *args, **kwargs):
        abs = getattr(cls, '__abstractmethods__', None)
        if abs:
            msg = "Can't instantiate abstract class {name} with abstract element{suffix} ({methods})"
            suffix = 's' if len(abs) > 1 else ''
            raise TypeError(msg.format(name=cls.__name__, suffix=suffix, methods=', '.join(abs)))
        # return super(EngineBase, cls).__new__(cls, *args, **kwargs)
        return super(EngineBase, cls).__new__(cls)
    #
    def __init__(self, *args, **kwargs):
        pass
