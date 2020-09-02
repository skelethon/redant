#!/usr/bin/env python

def is_callable(func, owner=None):
    ok, f = pick_function(func, owner)
    return ok


def pick_function(func, owner=None):
    #
    if isinstance(func, str):
        try:
            func = getattr(owner, func)
        except AttributeError as err:
            return False, None
    #
    return callable(func), func


def call_function(func, owner=None, *args, **kwargs):
    #
    if isinstance(func, str):
        try:
            func = getattr(owner, func)
        except AttributeError as err:
            raise err
    #
    if not callable(func):
        raise Exception("[func] is not callable")
    #
    return func(*args, **kwargs)
