#!/usr/bin/env python

from abc import abstractproperty, abstractmethod
from redant.engine import EngineBase
from redant.models.channels import ChannelEntity

class MessageConverter(EngineBase):
    #
    def __init__(self, *args, **kwargs):
        super(MessageConverter, self).__init__(*args, **kwargs)
    #
    @classmethod
    def __subclasshook__(cls, C):
        if cls is Controller:
            attrs = set(dir(C))
            if set(cls.__abstractmethods__) <= attrs:
                return True
            return NotImplemented


class MessagePublisher(EngineBase):
    #
    #
    def __init__(self, *args, **kwargs):
        super(MessagePublisher, self).__init__(*args, **kwargs)
    #
    #
    def _load_channels(self, channel_type=None):
        channels = ChannelEntity.find_all(channel_type=channel_type)
        return channels
    #
    #
    @classmethod
    def __subclasshook__(cls, C):
        if cls is Controller:
            attrs = set(dir(C))
            if set(cls.__abstractmethods__) <= attrs:
                return True
            return NotImplemented
