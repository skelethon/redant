#!/usr/bin/env python

import logging
import requests
import threading

from abc import abstractmethod
from redant.engine import EngineBase
from redant.utils.logging import getLogger

LOG = getLogger(__name__)

class RestClient(EngineBase):
    #
    #
    def __init__(self, *args, **kwargs):
        #
        self.__guard = RestGuard(self.auth_config)
        #
        self.__invokers = {}
        #
        for mapping in self.mappings:
            self.__invokers[mapping["name"]] = RestInvoker(mapping)
        #
        super(RestClient, self).__init__(*args, **kwargs)
    #
    #
    def invoke(self, entrypoint, input=None):
        if entrypoint not in self.__invokers:
            raise Exception('Rest entrypoint not found')
        #
        return self.__invokers[entrypoint].invoke(input)
    #
    #
    @property
    @abstractmethod
    def auth_config(self):
        pass
    #
    #
    @property
    @abstractmethod
    def mappings(self):
        pass
    #
    #
    @classmethod
    def __subclasshook__(cls, C):
        if cls is RestClient:
            attrs = set(dir(C))
            if set(cls.__abstractmethods__) <= attrs:
                return True
            return NotImplemented


class RestBearerAuth(requests.auth.AuthBase):
    #
    def __init__(self, token):
        self.__token = token
    #
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.__token
        return r


class RestGuard(object):
    #
    def __init__(self, auth_config, **kwargs):
        pass
    #
    #
    @property
    def available(self):
        return True
    #
    @property
    def access_token(self):
        #
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug('Thread[%s] get the access-token' % (threading.current_thread().ident))
    #
    @property
    def auth(self):
        #
        ## basic-auth
        #...
        #
        ## digest-authentication
        #...
        #
        ## if auth-mode is OAuth2
        return RestBearerAuth(self.access_token)


class RestInvoker(object):
    #
    #
    def __init__(self, mapping, guard=None, **kwargs):
        self.__mapping = mapping
        self.__guard = guard
        #
        self.__url = mapping['url']
        self.__method = mapping['method'] if 'method' in mapping else 'GET'
        #
        self.__i_transformer = RestInvoker.__extractCallable(mapping, 'i_transformer')
        self.__o_transformer = RestInvoker.__extractCallable(mapping, 'o_transformer')
    #
    #
    def invoke(self, input=None):
        #
        kwargs = self.sanitize(self.__i_transformer(input))
        #
        if self.__guard is not None and self.__guard.available:
            kwargs['auth'] = self.__guard.auth
        #
        r = requests.request(self.__method, self.__url, **kwargs)
        try:
            body = r.json()
        except JSONDecodeError as err:
            body = r.text
        #
        return self.__o_transformer(body=body, status_code=r.status_code, response=r)
    #
    #
    def sanitize(self, opts=dict()):
        return opts
    #
    #
    @classmethod
    def __extractCallable(cls, mapping, name, defaultFunc=None):
        if name in mapping and callable(mapping[name]):
            return mapping[name]
        if callable(defaultFunc):
            return defaultFunc
        return getattr(cls, '_' + name)
    #
    #
    def _i_transformer(data):
        if data is None:
            return dict()
        return dict(data=data)
    #
    def _o_transformer(body, status_code, response=None):
        return body
