#!/usr/bin/env python

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
