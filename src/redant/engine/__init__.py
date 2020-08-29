#!/usr/bin/env python

import logging

from abc import ABCMeta, abstractproperty, abstractmethod
from redant.utils.logging import getLogger
from redant.utils.object_util import json_dumps, json_loads
from redant.models.conversations import ConversationModel, ConversationSchema
from transitions import Machine

LOG = getLogger(__name__)

class Controller(object):
    __metaclass__ = ABCMeta

    def __init__(self, **kwargs):
        pass

    @classmethod
    def __subclasshook__(cls, C):
        if cls is Controller:
            attrs = set(dir(C))
            if set(cls.__abstractmethods__) <= attrs:
                return True
            return NotImplemented


class Flow(object):
    #
    __descriptor = None
    #
    def __init__(self, model, descriptor, phone_number):
        #
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug('PhoneNumber: [%s]' % phone_number)
        #
        assert isinstance(descriptor, Descriptor),\
            'descriptor object must be a Descriptor'
        self.__descriptor = descriptor
        #
        assert isinstance(model, Conversation) or model is None,\
            'model object is None or must be a Conversation'
        #
        # load the latest conversation
        current = ConversationModel.find_by_phone_number(phone_number)
        #
        # create one if not found
        if not current:
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug('The first conversation of [%s], create new persist object.' % phone_number)
            current = ConversationModel(phone_number=phone_number, state=descriptor.initial_state).create()
        else:
            # check the state and timeout
            if self.hasExpired(current, descriptor.states):
                if LOG.isEnabledFor(logging.DEBUG):
                    LOG.debug('The conversation[%s] has expired, create another' % phone_number)
                current = ConversationModel(phone_number=phone_number, state=descriptor.initial_state).create()
            else:
                if LOG.isEnabledFor(logging.DEBUG):
                    LOG.debug('The conversation[%s] is ok, continue ...' % phone_number)
            pass
        #
        if model is not None:
            model.descriptor = descriptor
            model.persist = current
        #
        # create the conversation transition
        self.machine = Machine(
            model=model,
            states=descriptor.states,
            transitions=descriptor.rules,
            initial=current.state)
        #
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug('A machine for [%s] has been created with state [%s]' % (phone_number, str(model.state)))
        #
        pass

    def hasExpired(self, conversation, states, timeout=3600*10):
        if conversation.state in [self.__descriptor.quit_state, self.__descriptor.done_state]:
            return True
        if not conversation.state in states:
            return True
        return False


class Conversation(object):
    __metaclass__ = ABCMeta

    __changed = False
    __context = dict()
    __persist = None
    __descriptor = None
    __final_states = []
    #
    #
    def __init__(self, **kwargs):
        pass
    #
    #
    @property
    def _context(self):
        return self.__context
    #
    #
    @property
    def descriptor(self):
        return NotImplemented
    #
    @descriptor.setter
    def descriptor(self, ref):
        #
        assert isinstance(ref, Descriptor), 'object must be a Descriptor'
        self.__descriptor = ref
        self.__final_states = [ self.__descriptor.done_state, self.__descriptor.quit_state ]
        #
        return ref
    #
    #
    @property
    def persist(self):
        return NotImplemented
    #
    @persist.setter
    def persist(self, ref):
        #
        assert isinstance(ref, ConversationModel), 'object must be a ConversationModel'
        self.__persist = ref
        #
        story = self.__persist.story
        if story is not None and len(story) > 0:
            story_dict, err = json_loads(story)
            if story_dict is not None:
                self.__context = story_dict
                if LOG.isEnabledFor(logging.DEBUG):
                    LOG.debug('loading the context successfully: %s' % json_dumps(self.__context))
            else:
                if LOG.isEnabledFor(logging.DEBUG):
                    LOG.debug('error on loading the context: %s' % str(err))
        #
        return ref
    #
    #
    def save_dialog(self):
        #
        if self.__persist is None:
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug('The persist object is None, skipped')
            return self
        #
        try:
            self.__persist.state = self.state
            #
            story_json = json_dumps(self.__context)
            self.__persist.story = story_json
            #
            self.__persist.save()
            #
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug('Logging current dialog successfully: %s' % story_json)
            return self
        except Exception as err:
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug('Logging current dialog failed, error: %s' % str(err))
            raise err
        pass
    #
    #
    def goodbye(self):
        if self._isInitialState() or self._isFinalState():
            return self
        try:
            self.__persist.state = self._quit_state
            #
            story_json = json_dumps(self.__context)
            self.__persist.story = story_json
            #
            self.__persist.save()
            #
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug('Logging farewell event successfully: %s' % story_json)
            return self
        except Exception as err:
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug('Logging farewell event failed, error: %s' % str(err))
            raise err
    #
    #
    def _isInitialState(self):
        return self.state == self._initial_state
    #
    def _isFinalState(self):
        return self.state in self.__final_states
    #
    @property
    def _initial_state(self):
        return self.__descriptor.initial_state
    #
    @property
    def _done_state(self):
        return self.__descriptor.done_state
    #
    @property
    def _quit_state(self):
        return self.__descriptor.quit_state
    #
    #
    @classmethod
    def __subclasshook__(cls, C):
        if cls is Conversation:
            attrs = set(dir(C))
            if set(cls.__abstractmethods__) <= attrs:
                return True
            return NotImplemented


class Descriptor(object):
    __metaclass__ = ABCMeta
    #
    __rules = None
    #
    def __init__(self, **kwargs):
        #
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug('The states: %s' % json_dumps(self.states))
        #
        self.__rules = self.enhanceRules(self.transitions)
        pass
    #
    @abstractproperty
    def states(self):
        pass
    #
    @abstractproperty
    def initial_state(self):
        pass
    #
    @abstractproperty
    def done_state(self):
        pass
    #
    @abstractproperty
    def quit_state(self):
        pass
    #
    @abstractproperty
    def transitions(self):
        pass
    #
    ##
    @property
    def rules(self):
        return self.__rules
    #
    ##
    @classmethod
    def enhanceRules(cls, transitions):
        if not isinstance(transitions, list):
            return transitions
        #
        for transition in transitions:
            #
            if 'trigger' not in transition:
                transition['trigger'] = 'next'
            #
            cls.__assertListItem(transition, 'before', 'transition_before')
            cls.__assertListItem(transition, 'after', 'save_dialog', position=0)
            cls.__assertListItem(transition, 'after', 'transition_after')
            #
            if 'target' in transition:
                transition['dest'] = transition['target']
                del transition['target']
        #
        return transitions
    #
    ##
    @staticmethod
    def __assertListItem(obj, list_name, item, position=None):
        if not obj:
            return obj
        if list_name not in obj:
            obj[list_name] = []
        if not isinstance(obj[list_name], list):
            obj[list_name] = [ obj[list_name] ]
        if item not in obj[list_name]:
            if isinstance(position, int) and position < len(obj[list_name]):
                obj[list_name].insert(position, item)
            else:
                obj[list_name].append(item)
        return obj
    #
    ##
    @classmethod
    def __subclasshook__(cls, C):
        if cls is Descriptor:
            attrs = set(dir(C))
            if set(cls.__abstractmethods__) <= attrs:
                return True
            return NotImplemented
