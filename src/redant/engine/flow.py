#!/usr/bin/env python

import pytz

from abc import abstractproperty, abstractmethod
from datetime import datetime, timedelta
from redant.engine import EngineBase
from redant.engine.adapters import MessageConverter, MessagePublisher
from redant.utils.function_util import is_callable, call_function
from redant.utils.logging import getLogger, LogLevel as LL
from redant.utils.object_util import json_dumps, json_loads
from redant.models.conversations import ConversationEntity, ConversationSchema
from transitions import Machine

LOG = getLogger(__name__)
SILENT_MESSAGE = (None, None)


class Controller(EngineBase):
    #
    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self.__converters = dict()
    #
    #
    def register(self, adapter):
        if isinstance(adapter, MessageConverter):
            if LOG.isEnabledFor(LL.DEBUG):
                LOG.log(LL.DEBUG, 'converter[%s] has been registered' % adapter.channel_type)
            self.__converters[adapter.channel_type] = adapter
        return self
    #
    #
    def get_converter(self, name):
        if name not in self.__converters:
            return None,  ValueError('converter not found')
        return self.__converters[name], None
    #
    #
    @classmethod
    def __subclasshook__(cls, C):
        if cls is Controller:
            attrs = set(dir(C))
            if set(cls.__abstractmethods__) <= attrs:
                return True
            return NotImplemented


class Observer(EngineBase):
    def __init__(self, *args, **kwargs):
        self.__publishers = dict()
        super().__init__(*args, **kwargs)
    #
    #
    def register(self, adapter):
        if isinstance(adapter, MessagePublisher):
            if LOG.isEnabledFor(LL.DEBUG):
                LOG.log(LL.DEBUG, 'publisher[%s] has been registered' % adapter.channel_type)
            self.__publishers[adapter.channel_type] = adapter
        return self
    #
    #
    def get_publisher(self, name):
        if name not in self.__publishers:
            return None,  ValueError('publisher not found')
        return self.__publishers[name], None
    #
    #
    @classmethod
    def __subclasshook__(cls, C):
        if cls is Observer:
            attrs = set(dir(C))
            if set(cls.__abstractmethods__) <= attrs:
                return True
            return NotImplemented


class Conversation(EngineBase):
    #
    __channel_code = None
    __chatter_code = None
    __phone_number = None
    __context = dict()
    __persist = None
    __timezone = None
    __descriptor = None
    __flow = None
    #
    #
    def __init__(self, channel_code, chatter_code, phone_number, descriptor=None, **kwargs):
        #
        self.__channel_code = channel_code
        self.__chatter_code = chatter_code
        self.__phone_number = phone_number
        #
        assert isinstance(descriptor, Descriptor), 'descriptor argument must be a Descriptor'
        self.__descriptor = descriptor
        #
        self.__flow = _Flow(conversation = self)
        #
        super(Conversation, self).__init__(**kwargs)
    #
    #
    @property
    def _context(self):
        return self.__context
    #
    #
    @property
    def channel_code(self):
        return self.__channel_code
    #
    @property
    def chatter_code(self):
        return self.__chatter_code
    #
    @property
    def phone_number(self):
        return self.__phone_number
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
        assert isinstance(ref, ConversationEntity), 'object must be a ConversationEntity'
        self.__persist = ref
        #
        story = self.__persist.story
        if story is not None and len(story) > 0:
            story_dict, err = json_loads(story)
            if story_dict is not None:
                self.__context = story_dict
                if LOG.isEnabledFor(LL.DEBUG):
                    LOG.log(LL.DEBUG, 'loading the context successfully: %s' % json_dumps(self.__context))
            else:
                if LOG.isEnabledFor(LL.DEBUG):
                    LOG.log(LL.DEBUG, 'error on loading the context: %s' % str(err))
        #
        return ref
    #
    #
    @property
    def timezone(self):
        if self.__timezone is None:
            if isinstance(self.__persist, ConversationEntity):
                try:
                    self.__timezone = pytz.timezone(self.__persist.timezone)
                except pytz.exceptions.UnknownTimeZoneError as err:
                    raise errors.InvalidTimeZoneError('Unknown timezone[%s]' % str(self.__persist.timezone))
            if self.__timezone is None:
                raise errors.InvalidTimeZoneError('timezone is None')
        return self.__timezone
    #
    @property
    def timezone_name(self):
        return self.timezone.tzname(None)
    #
    #
    @property
    def _email(self):
        if self.__persist is None:
            return None
        if self.__persist.chatter is None:
            return None
        return self.__persist.chatter.email
    #
    @property
    def _first_name(self):
        if self.__persist is None:
            return None
        if self.__persist.chatter is None:
            return None
        return self.__persist.chatter.first_name
    #
    @property
    def _last_name(self):
        if self.__persist is None:
            return None
        if self.__persist.chatter is None:
            return None
        return self.__persist.chatter.last_name
    #
    @property
    def _banned(self):
        if self.__persist is None:
            return False
        if self.__persist.chatter is None:
            return False
        return self.__persist.chatter.banned == True
    #
    #
    def _count_cancellations(self, range_size=1, range_unit='hours'):
        #
        tdargs = dict()
        tdargs[range_unit] = range_size
        #
        latest_creation_time = datetime.utcnow() - timedelta(**tdargs)
        r = ConversationEntity.count_by__channel__chatter(
            channel_code=self.channel_code,
            chatter_code=self.chatter_code,
            overall_status=-2,
            latest_creation_time=latest_creation_time
        )
        #
        return r
    #
    #
    def save_dialog(self):
        #
        if self.__persist is None:
            if LOG.isEnabledFor(LL.DEBUG):
                LOG.log(LL.DEBUG, 'The persist object is None, skipped')
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
            if LOG.isEnabledFor(LL.DEBUG):
                LOG.log(LL.DEBUG, 'Logging current dialog successfully: %s', story_json)
            return self
        except Exception as err:
            if LOG.isEnabledFor(LL.DEBUG):
                LOG.log(LL.DEBUG, 'Logging current dialog failed, error: %s', str(err))
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
            if LOG.isEnabledFor(LL.DEBUG):
                LOG.log(LL.DEBUG, 'Logging stop event successfully: %s', story_json)
            return self
        except Exception as err:
            if LOG.isEnabledFor(LL.DEBUG):
                LOG.log(LL.DEBUG, 'Logging stop event failed, error: %s', str(err))
            raise err
    #
    #
    def next_action(self):
        #
        ## force quit
        #
        force_quit, reply_on_quit = self._force_quit
        if force_quit:
            self.goodbye()
            return reply_on_quit
        #
        ## Cancellation
        #
        if self.__is_cancellation_confirming:
            #
            matched, msgs = self._cancellation_accepted
            if LOG.isEnabledFor(LL.DEBUG):
                LOG.log(LL.DEBUG, '_cancellation_accepted -> [%s]: %s', str(matched), str(msgs))
            if matched:
                self.__on_cancellation_accepted()
                return msgs
            #
            matched, msgs = self._cancellation_rejected
            if LOG.isEnabledFor(LL.DEBUG):
                LOG.log(LL.DEBUG, '_cancellation_rejected -> [%s]: %s', str(matched), str(msgs))
            if matched:
                self.__on_cancellation_rejected()
                return msgs
            #
            return self._cancellation_prompt
        #
        canreq, reply_on_canreq = self._cancellation_requested
        if canreq:
            self.__on_cancellation_requested()
            return reply_on_canreq
        #
        ##
        #
        if self.state in self._internal_states:
            return self._in_progress_prompt
        #
        ##
        #
        guide_matched, guide_content = self._help
        if guide_matched:
            guide_func = 'help__' + self.state
            if is_callable(guide_func, self):
                return call_function(guide_func, self)
            return guide_content
        #
        ## normal flow
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
        return SILENT_MESSAGE
    #
    #
    def next_prompt(self):
        #
        ## normal flow
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
        return SILENT_MESSAGE
    #
    #
    def transition_before(self):
        if LOG.isEnabledFor(LL.DEBUG):
            LOG.log(LL.DEBUG, 'Before transition from state: [%s]' % self.state)
    #
    def transition_after(self):
        if LOG.isEnabledFor(LL.DEBUG):
            LOG.log(LL.DEBUG, 'After transition to state: [%s]' % self.state)
    #
    #
    def _isInitialState(self):
        return self.state == self._initial_state
    #
    def _isFinalState(self):
        return self.state in self._final_states or self.state == self._quit_state
    #
    @property
    def _initial_state(self):
        return self.__descriptor.initial_state
    #
    @property
    def _quit_state(self):
        return self.__descriptor.quit_state
    #
    @property
    def _internal_states(self):
        return self.__descriptor.internal_states
    #
    @property
    def _final_states(self):
        return self.__descriptor.final_states
    #
    @property
    def _in_progress_prompt(self):
        return SILENT_MESSAGE
    #
    @property
    def _force_quit(self):
        return False, SILENT_MESSAGE
    #
    #
    @property
    def _cancellation_requested(self):
        return False, SILENT_MESSAGE
    #
    def __on_cancellation_requested(self):
        return self.__switch_cancellation_status(-1)
    #
    @property
    def __is_cancellation_confirming(self):
        return self.__persist.overall_status == -1
    #
    @property
    def _cancellation_accepted(self):
        return False, SILENT_MESSAGE
    #
    def __on_cancellation_accepted(self):
        return self.__switch_cancellation_status(-2)
    #
    @property
    def _cancellation_rejected(self):
        return False, SILENT_MESSAGE
    #
    def __on_cancellation_rejected(self):
        return self.__switch_cancellation_status(0)
    #
    @property
    def _cancellation_prompt(self):
        return SILENT_MESSAGE
    #
    def __switch_cancellation_status(self, status):
        try:
            self.__persist.overall_status = status
            #
            self.__persist.save()
            #
            if LOG.isEnabledFor(LL.DEBUG):
                LOG.log(LL.DEBUG, '__switch_cancellation_status(%s) action has done successfully' % str(status))
            return self
        except Exception as err:
            if LOG.isEnabledFor(LL.DEBUG):
                LOG.log(LL.DEBUG, '__switch_cancellation_status action has failed, error: %s' % str(err))
            raise err
    #
    #
    @property
    def _help(self):
        return False, SILENT_MESSAGE
    #
    #
    @classmethod
    def __subclasshook__(cls, C):
        if cls is Conversation:
            attrs = set(dir(C))
            if set(cls.__abstractmethods__) <= attrs:
                return True
            return NotImplemented


class Descriptor(EngineBase):
    #
    __rules = None
    __replies = None
    #
    def __init__(self, *args, **kwargs):
        #
        if LOG.isEnabledFor(LL.DEBUG):
            LOG.log(LL.DEBUG, 'The states: %s' % json_dumps(self.states))
        #
        self.__rules, self.__replies = self.enhanceRules(self.transitions)
        #
        super(Descriptor, self).__init__(*args, **kwargs)
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
    def quit_state(self):
        pass
    #
    @abstractproperty
    def internal_states(self):
        pass
    #
    @abstractproperty
    def final_states(self):
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
            if 'reply' in transition:
                replies[transition['source'] + '__' + transition['target']] = transition['reply']
                del transition['reply']
            #
            if 'target' in transition:
                transition['dest'] = transition['target']
                del transition['target']
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


class _Flow(object):
    #
    __conversation = None
    __descriptor = None
    #
    def __init__(self, conversation):
        #
        #
        assert isinstance(conversation, Conversation), 'conversation argument must be a Conversation'
        self.__conversation = conversation
        self.__descriptor = self.__conversation.descriptor
        #
        # load the latest conversation
        current = ConversationEntity.find_by__channel__chatter(conversation.channel_code, conversation.chatter_code)
        #
        # create one if not found
        kwargs = dict(
            channel_code=conversation.channel_code,
            chatter_code=conversation.chatter_code,
            phone_number=conversation.phone_number,
            state=self.__descriptor.initial_state
        )
        conver_label = conversation.chatter_code + ' -> ' + conversation.channel_code
        #
        if not current:
            if LOG.isEnabledFor(LL.DEBUG):
                LOG.log(LL.DEBUG, 'The first conversation of [%s], create new persist object.' % conver_label)
            current = ConversationEntity(**kwargs).create()
        else:
            # check the state and timeout
            if self.hasExpired(current, self.__descriptor):
                if LOG.isEnabledFor(LL.DEBUG):
                    LOG.log(LL.DEBUG, 'The conversation[%s] has expired, create another' % conver_label)
                current = ConversationEntity(**kwargs).create()
            else:
                if LOG.isEnabledFor(LL.DEBUG):
                    LOG.log(LL.DEBUG, 'The conversation[%s] is ok, continue ...' % conver_label)
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
        if LOG.isEnabledFor(LL.DEBUG):
            LOG.log(LL.DEBUG, 'A machine for [%s] has been created with state [%s]' % (conver_label, str(conversation.state)))
        #
        pass
    #
    def __has_cancelled(self, persist):
        if persist.overall_status <= -2:
            if LOG.isEnabledFor(LL.DEBUG):
                LOG.log(LL.DEBUG, 'The user has cancelled the task')
            return True
        return False
    #
    def __has_done(self, persist):
        if persist.state in self.__descriptor.final_states:
            if LOG.isEnabledFor(LL.DEBUG):
                LOG.log(LL.DEBUG, 'The conversation has finished')
            return True
        return False
    #
    def __has_quit(self, persist):
        if persist.state == self.__descriptor.quit_state:
            if LOG.isEnabledFor(LL.DEBUG):
                LOG.log(LL.DEBUG, 'The user has quit this conversation')
            return True
        return False
    #
    def __is_invalid_state(self, persist):
        if not persist.state in self.__descriptor.states:
            if LOG.isEnabledFor(LL.DEBUG):
                LOG.log(LL.DEBUG, 'The conversation has invalid state [%s] / valid states: %s' % 
                    (persist.state, json_dumps(self.__descriptor.states)))
            return True
        return False
    #
    def hasExpired(self, persist, descriptor, timeout=3600*10):
        return any([
            self.__has_cancelled(persist),
            self.__has_done(persist),
            self.__has_quit(persist),
            self.__is_invalid_state(persist)
        ])
