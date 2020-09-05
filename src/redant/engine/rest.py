#!/usr/bin/env python

import logging
import requests

from abc import ABCMeta, abstractproperty, abstractmethod
from redant.utils.logging import getLogger

LOG = getLogger(__name__)

class RestClient(object):
    __metaclass__ = ABCMeta
    #
    #
    def __init__(self, **kwargs):
        #
        self.__invokers = {}
        #
        for mapping in self.mappings:
            self.__invokers[mapping["name"]] = RestInvoker(mapping)
    #
    #
    def invoke(self, entrypoint, input=None):
        if entrypoint not in self.__invokers:
            raise Exception('Rest entrypoint not found')
        #
        return self.__invokers[entrypoint].invoke(input)
    #
    #
    @abstractproperty
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


class RestInvoker(object):
    #
    #
    def __init__(self, mapping, **kwargs):
        self.__mapping = mapping
        #
        self.__url = mapping['url']
        self.__method = mapping['method'] if 'method' in mapping else 'GET'
        #
        self.__i_transformer = RestInvoker.__extractCallable(mapping, 'i_transformer')
        self.__o_transformer = RestInvoker.__extractCallable(mapping, 'o_transformer')
    #
    #
    def invoke(self, input=None):
        kwargs = self.sanitize(self.__i_transformer(input))
        r = requests.request(self.__method, self.__url, **kwargs)
        try:
            body = r.json()
        except JSONDecodeError as err:
            body = r.text
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
