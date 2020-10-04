#!/usr/bin/env python

import os
import requests
import threading

from abc import abstractmethod
from redant.engine import EngineBase
from redant.utils.logging import getLogger, LogLevel as LL
from redant.utils.net_util import url_build
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
            self.__guard = RestGuard(**self.auth_config)
        #
        mappings = self.mappings
        assert isinstance(mappings, dict), "mappings must be a dict"
        #
        entrypoints = mappings['entrypoints'] if 'entrypoints' in mappings else []
        assert isinstance(entrypoints, list), "mappings['entrypoints'] must be a list"
        #
        for entrypoint in entrypoints:
            self.__invokers[entrypoint["name"]] = RestInvoker(entrypoint=entrypoint, guard=self.__guard)
        #
        super(RestClient, self).__init__(*args, **kwargs)
    #
    #
    def invoke(self, entrypoint_name, input=None):
        if entrypoint_name not in self.__invokers:
            raise Exception('Rest entrypoint not found')
        #
        return self.__invokers[entrypoint_name].invoke(input)
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
    __name = None
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
    def __init__(self, name, auth_args, **kwargs):
        assert isinstance(name, str), 'name must be a string'
        self.__name = name
        #
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
            self.__authenticator = RestInvoker(entrypoint=auth_args, guard=None)
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
    def __init__(self, entrypoints=dict(), default=None, **kwargs):
        #
        assert isinstance(entrypoints, dict), "entrypoints must be a dict"
        assert default is None or (isinstance(default, str) and default in entrypoints),\
                "[default] must be None or a key of entrypoints"
        #
        if default is not None:
            self.__auth_default = default
        #
        if isinstance(entrypoints, dict):
            for auth_name in entrypoints.keys():
                auth_args = entrypoints[auth_name]
                self.__auths[auth_name] = AuthBuilder(auth_name, auth_args)
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
    def __init__(self, entrypoint, guard=None, **kwargs):
        self.__entrypoint = entrypoint
        self.__guard = guard
        #
        self.__auth_name = entrypoint['auth_name'] if 'auth_name' in entrypoint else None
        #
        if isinstance(entrypoint['url'], str):
            self.__url = entrypoint['url']
        elif isinstance(entrypoint['url'], dict):
            self.__url = url_build(**entrypoint['url'])
        #
        self.__method = entrypoint['method'] if 'method' in entrypoint else 'GET'
        #
        self.__body = entrypoint['body'] if 'body' in entrypoint else None
        #
        self.__body_as_json = not ('body_as_json' in entrypoint and entrypoint['body_as_json'] is False)
        #
        self.__i_transformer = RestInvoker.__extractCallable(entrypoint, 'i_transformer')
        self.__o_transformer = RestInvoker.__extractCallable(entrypoint, 'o_transformer')
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
        if 'body' not in kwargs and self.__body is not None:
            kwargs['body'] = self.__body
        #
        if 'body' in kwargs:
            if self.__body_as_json:
                kwargs['json'] = kwargs['body']
            else:
                kwargs['data'] = kwargs['body']
            #
            del kwargs['body']
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
    def __extractCallable(cls, entrypoint, name, defaultFunc=None):
        if name in entrypoint and callable(entrypoint[name]):
            return entrypoint[name]
        if callable(defaultFunc):
            return defaultFunc
        return getattr(cls, '_' + name)
    #
    #
    def _i_transformer(data=None):
        if data is None:
            return dict()
        return dict(body=data)
    #
    def _o_transformer(body, status_code, response=None):
        return body
