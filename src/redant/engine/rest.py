#!/usr/bin/env python

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
    __guard = None
    __invokers = dict()
    #
    #
    def __init__(self, *args, **kwargs):
        #
        if self.auth_config is not None and len(self.auth_config) > 0:
            self.__guard = RestGuard(self.auth_config)
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
        if LOG.isEnabledFor(LL.DEBUG):
            LOG.log(LL.DEBUG, 'Inject the Bearer-Access-Token into authorization header')
        return r


class AuthBuilder(object):
    #
    __available = True
    #
    ## Basic/Digest Authentication
    __basic_auth = None
    __digest_auth = None
    #
    ## Oauth2/Bearer Authentication
    __authenticator = None
    __access_token = None
    __credentials = None
    #
    #
    def __init__(self, auth_args, **kwargs):
        assert isinstance(auth_args, dict), 'auth_args must be a dict'
        #
        self.__available = not 'enabled' in auth_args or auth_args['enabled']
        if not self.__available:
            return
        #
        auth_type = auth_args['auth_type']
        if auth_type == BASIC_AUTH:
            self.__basic_auth = HTTPBasicAuth(auth_args['username'], auth_args['password'])
        if auth_type == DIGEST_AUTH:
            self.__basic_auth = HTTPDigestAuth(auth_args['username'], auth_args['password'])
        if auth_type in [BEARER_AUTH, 'oauth2']:
            self.__authenticator = RestInvoker(mapping=auth_args, guard=None)
            self.__credentials = None
        pass
    #
    #
    @property
    def available(self):
        return self.__available
    #
    @property
    def auth(self):
        if not self.__available:
            return None
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
    #
    @property
    def access_token(self):
        #
        injected_token = os.getenv('REDANT_BEARER_ACCESS_TOKEN', None)
        if injected_token and len(injected_token) > 1:
            if LOG.isEnabledFor(LL.DEBUG):
                LOG.log(LL.DEBUG, 'Inject value from the environment variable to the Bearer-Access-Token')
            return injected_token
        if self.__access_token is None:
            if LOG.isEnabledFor(LL.DEBUG):
                LOG.log(LL.DEBUG, 'The access_token not found, request a new credentials')
            if self.__authenticator is not None:
                result = self.__authenticator.invoke()
                if isinstance(result, dict):
                    if 'access_token' in result:
                        self.__access_token = result['access_token']
        return self.__access_token


class RestGuard(object):
    #
    __auths = dict()
    __auth_default = None
    #
    def __init__(self, auth_config, **kwargs):
        if isinstance(auth_config, dict):
            for auth_name in auth_config.keys():
                auth_args = auth_config[auth_name]
                self.__auths[auth_name] = AuthBuilder(auth_args)
                if self.__auth_default is None:
                    self.__auth_default = auth_name
        pass
    #
    def getAuth(self, auth_name):
        if auth_name is None:
            auth_name = self.__auth_default
        if auth_name not in self.__auths:
            return None
        return self.__auths[auth_name].auth


class RestInvoker(object):
    #
    #
    def __init__(self, mapping, guard=None, **kwargs):
        self.__mapping = mapping
        self.__guard = guard
        #
        self.__auth_name = mapping['auth_name'] if 'auth_name' in mapping else None
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
        if self.__guard is not None:
            auth = self.__guard.getAuth(self.__auth_name)
            if auth is not None:
                kwargs['auth'] = auth
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
