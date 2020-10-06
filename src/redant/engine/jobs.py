#!/usr/bin/env python3

import atexit
import time
import os
import sys

from datetime import datetime
from pytz import utc

from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from redant.utils.logging import getLogger, LogLevel as LL


LOG = getLogger(__name__)


class ConversationScanner():
    #
    def __init__(self, listener, *args, **kwargs):
        #
        executors = {
            'default': ThreadPoolExecutor(20),
            'processpool': ProcessPoolExecutor(5)
        }
        #
        jobstores = {
            'default': SQLAlchemyJobStore(url='mysql+pymysql://chatbot:Zaq!23EdcX@localhost:3306/cronjob')
        }
        #
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }
        #
        self.__scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc)
        #
        self.__job = self.__scheduler.add_job(listener, 'interval', seconds=7, id='engagement_checking_job', replace_existing=True)
        #
        atexit.register(self.shutdown)
    #
    #
    def start(self):
        if self.__scheduler is not None and not self.__scheduler.running:
            self.__scheduler.start()
        if LOG.isEnabledFor(LL.DEBUG):
            LOG.log(LL.DEBUG, 'ConversationScanner.start() started')
        return self
    #
    #
    def shutdown(self):
        if self.__scheduler is not None and self.__scheduler.running:
            if self.__scheduler.get_job('engagement_checking_job') is not None:
                self.__scheduler.remove_job(job_id='engagement_checking_job')
            self.__scheduler.shutdown()
        if LOG.isEnabledFor(LL.DEBUG):
            LOG.log(LL.DEBUG, 'ConversationScanner.shutdown() finished')
        return self
