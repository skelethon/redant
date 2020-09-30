#!/usr/bin/env python3

class RedantError(RuntimeError):
    def __init__(self, *args, **kwargs):
        super(RedantError, self).__init__(self,*args,**kwargs)

class ModelArgumentError(RedantError):
    def __init__(self, *args, **kwargs):
        super(ModelArgumentError, self).__init__(self,*args,**kwargs)

class ChannelNotFoundError(RedantError):
    def __init__(self, *args, **kwargs):
        super(ChannelNotFoundError, self).__init__(self,*args,**kwargs)
