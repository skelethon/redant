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

class InvalidTimeZoneError(RedantError):
    def __init__(self, *args, **kwargs):
        super(InvalidTimeZoneError, self).__init__(self,*args,**kwargs)

class RestInvocationError(RedantError):
    def __init__(self, *args, **kwargs):
        super(RestInvocationError, self).__init__(self,*args,**kwargs)

class RestProcessingError(RedantError):
    def __init__(self, *args, **kwargs):
        super(RestProcessingError, self).__init__(self,*args,**kwargs)

class RestStatusCodeError(RedantError):
    def __init__(self, *args, **kwargs):
        super(RestStatusCodeError, self).__init__(self,*args,**kwargs)

class RestReturnBodyError(RedantError):
    def __init__(self, *args, **kwargs):
        super(RestReturnBodyError, self).__init__(self,*args,**kwargs)
