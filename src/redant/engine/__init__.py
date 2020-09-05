#!/usr/bin/env python

import logging
import requests

from abc import ABCMeta, abstractproperty, abstractmethod
from redant.utils.function_util import is_callable, call_function
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
    __conversation = None
    __descriptor = None
    #
    def __init__(self, conversation, phone_number):
        #
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug('PhoneNumber: [%s]' % phone_number)
        #
        #
        assert isinstance(conversation, Conversation), 'conversation argument must be a Conversation'
        self.__conversation = conversation
        self.__descriptor = self.__conversation.descriptor
        #
        # load the latest conversation
        current = ConversationModel.find_by_phone_number(phone_number)
        #
        # create one if not found
        if not current:
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug('The first conversation of [%s], create new persist object.' % phone_number)
            current = ConversationModel(phone_number=phone_number, state=self.__descriptor.initial_state).create()
        else:
            # check the state and timeout
            if self.hasExpired(current, self.__descriptor):
                if LOG.isEnabledFor(logging.DEBUG):
                    LOG.debug('The conversation[%s] has expired, create another' % phone_number)
                current = ConversationModel(phone_number=phone_number, state=self.__descriptor.initial_state).create()
            else:
                if LOG.isEnabledFor(logging.DEBUG):
                    LOG.debug('The conversation[%s] is ok, continue ...' % phone_number)
            pass
        #
        #
        self.__conversation.persist = current
        #
        # create the conversation transition
        self.machine = Machine(
            model=conversation,
            states=self.__descriptor.states,
            transitions=self.__descriptor.rules,
            initial=current.state)
        #
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug('A machine for [%s] has been created with state [%s]' % (phone_number, str(conversation.state)))
        #
        pass

    def hasExpired(self, conversation, descriptor, timeout=3600*10):
        if conversation.state in [descriptor.quit_state, descriptor.done_state]:
            return True
        if not conversation.state in descriptor.states:
            return True
        return False


class Conversation(object):
    __metaclass__ = ABCMeta

    __changed = False
    __context = dict()
    __persist = None
    __descriptor = None
    __final_states = []
    __flow = None
    #
    #
    def __init__(self, descriptor=None, phone_number=None, **kwargs):
        #
        assert isinstance(descriptor, Descriptor), 'descriptor argument must be a Descriptor'
        self.__descriptor = descriptor
        self.__final_states = [ self.__descriptor.done_state, self.__descriptor.quit_state ]
        #
        self.__flow = Flow(conversation = self, phone_number = phone_number)
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
        return self.__descriptor
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
    def next_action(self):
        #
        from_state = self.state
        self._next()
        to_state = self.state
        #
        kwargs = dict(from_state=from_state)
        #
        replies = self.__descriptor.replies
        reply_name = from_state + '__' + to_state
        if reply_name in replies and isinstance(replies[reply_name], str):
            reply_func = replies[reply_name]
            return call_function(reply_func, self, **kwargs)
        #
        reply_func = 'reply__' + reply_name
        if is_callable(reply_func, self):
            return call_function(reply_func, self, **kwargs)
        #
        reply_func = 'reply__' + self.state
        if is_callable(reply_func, self):
            return call_function(reply_func, self, **kwargs)
        #
        return None, None
    #
    #
    def transition_before(self):
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug('Before transition from state: [%s]' % self.state)
    #
    def transition_after(self):
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug('After transition to state: [%s]' % self.state)
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
    __replies = None
    #
    def __init__(self, **kwargs):
        #
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug('The states: %s' % json_dumps(self.states))
        #
        self.__rules, self.__replies = self.enhanceRules(self.transitions)
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
    @property
    def replies(self):
        return self.__replies
    #
    ##
    @classmethod
    def enhanceRules(cls, transitions):
        if not isinstance(transitions, list):
            return transitions
        #
        replies = dict()
        #
        for transition in transitions:
            #
            if 'trigger' not in transition:
                transition['trigger'] = '_next'
            #
            cls.__assertListItem(transition, 'before', 'transition_before')
            cls.__assertListItem(transition, 'after', 'save_dialog', position=0)
            cls.__assertListItem(transition, 'after', 'transition_after')
            #
            if 'target' in transition:
                transition['dest'] = transition['target']
                del transition['target']
            #
            if 'reply' in transition:
                replies[transition['source'] + '__' + transition['dest']] = transition['reply']
                del transition['reply']
        #
        return transitions, replies
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
