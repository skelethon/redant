#!/usr/bin/env python

import logging
import os
from flask import has_request_context, request
from flask.logging import default_handler

logFormater = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

streamHandler = logging.StreamHandler()
streamHandler.setLevel(logging.DEBUG)
streamHandler.setFormatter(logFormater)

def getLogger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(streamHandler)
    return logger

def disableFlaskLog(app):
    logger = logging.getLogger('werkzeug')
    logger.disabled = True
    app.logger.disabled = True

def injectLogMessage(msgIdFieldName):
    formatter = RequestFormatter(
        msgIdFieldName,
        '%(asctime)s - %(message_id)s - %(levelname)s - %(name)s - %(message)s'
    )
    default_handler.setFormatter(formatter)
    streamHandler.setFormatter(formatter)

class RequestFormatter(logging.Formatter):
    def __init__(self, msgIdFieldName, *args):
        self.__msgIdFieldName = msgIdFieldName
        super().__init__(*args)

    def format(self, record):
        if has_request_context():
            record.message_id = request.values.get(self.__msgIdFieldName, '')
            record.remote_addr = request.remote_addr
        else:
            record.message_id = None
            record.remote_addr = None
        return super().format(record)


class LogLevel:
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    VERBOSE = logging.DEBUG
    NOTSET = logging.NOTSET


STEP_STOP_LINE = None

def printStepStop(LOG):
    if os.getenv('REDANT_STEP_STOP'):
        if LOG.isEnabledFor(logging.DEBUG):
            global STEP_STOP_LINE
            if STEP_STOP_LINE is None:
                STEP_STOP_LINE = ''.rjust(80, '=')
            LOG.debug(STEP_STOP_LINE)
