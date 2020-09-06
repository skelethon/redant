#!/usr/bin/env python

import logging
import os
import requests
import threading

from abc import abstractmethod
from redant.engine import EngineBase
from redant.utils.logging import getLogger, LogLevel as LL
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

BASIC_AUTH = 'basic'
DIGEST_AUTH = 'digest'
BEARER_AUTH = 'bearer'

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
            self.__invokers[mapping["name"]] = RestInvoker(mapping, guard=self.__guard)
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


class BearerAuth(requests.auth.AuthBase):
    #
    def __init__(self, token):
        self.__token = token
        if LOG.isEnabledFor(LL.VERBOSE):
            LOG.log(LL.VERBOSE, 'Create a BearerAuth object from the token [%s]' % self.__token)
    #
    def __call__(self, r):
        bearer_token = r.headers["authorization"] = "Bearer " + self.__token
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.log(logging.DEBUG, 'Inject the Bearer-Access-Token into authorization header')
        return r


class RestGuard(object):
    #
    ## Basic/Digest Authentication
    __basic_auth = None
    __digest_auth = None
    #
    ## Oauth2/Bearer Authentication
    __authenticator = None
    __credentials = None
    #
    #
    def __init__(self, auth_config, **kwargs):
        if isinstance(auth_config, dict):
            for auth_type in auth_config.keys():
                auth_args = auth_config[auth_type]
                if auth_type == BASIC_AUTH:
                    if not 'enabled' in auth_args or not auth_args['enabled']:
                        self.__basic_auth = HTTPBasicAuth(auth_args['username'], auth_args['password'])
                if auth_type == DIGEST_AUTH:
                    if not 'enabled' in auth_args or not auth_args['enabled']:
                        self.__basic_auth = HTTPDigestAuth(auth_args['username'], auth_args['password'])
                if auth_type in ['bearer', 'oauth2']:
                    mapping = auth_config[auth_type]
                    self.__authenticator = RestInvoker(mapping, guard=None)
                    self.__access_token = None
                    self.__credentials = None
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
        injected_token = os.getenv('REDANT_BEARER_ACCESS_TOKEN', None)
        if injected_token and len(injected_token) > 1:
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug('Inject value from the environment variable to the Bearer-Access-Token')
            return injected_token
        if self.__access_token is None:
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug('')
            result = self.__authenticator.invoke()
            if isinstance(result, dict):
                if 'access_token' in result:
                    self.__access_token = result['access_token']
        return self.__access_token
    #
    @property
    def auth(self):
        #
        ## basic-auth
        if self.__basic_auth is not None:
            return self.__basic_auth
        #
        ## digest-authentication
        if self.__digest_auth is not None:
            return self.__digest_auth
        #
        ## if auth-mode is OAuth2
        return BearerAuth(self.access_token)


class RestInvoker(object):
    #
    #
    def __init__(self, mapping, guard=None, **kwargs):
        self.__mapping = mapping
        self.__guard = guard
        #
        self.__url = mapping['url']
        self.__method = mapping['method'] if 'method' in mapping else 'GET'
        self.__data = mapping['data'] if 'data' in mapping else None
        #
        self.__i_transformer = RestInvoker.__extractCallable(mapping, 'i_transformer')
        self.__o_transformer = RestInvoker.__extractCallable(mapping, 'o_transformer')
    #
    #
    def invoke(self, *args, **kwargs):
        #
        kwargs = self.sanitize(self.__i_transformer(*args, **kwargs))
        #
        if self.__guard is not None and self.__guard.available:
            kwargs['auth'] = self.__guard.auth
        #
        if 'data' not in kwargs and self.__data is not None:
            kwargs['data'] = self.__data
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
    def _i_transformer(data=None):
        if data is None:
            return dict()
        return dict(data=data)
    #
    def _o_transformer(body, status_code, response=None):
        return body
