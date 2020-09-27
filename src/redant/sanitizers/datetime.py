#!/usr/bin/env python

import re
import pendulum
import pytz

from datetime import datetime, timedelta

class TimeSanitizer(object):
    #
    def __init__(self, timezone=None):
        self.__timezone = timezone
    #
    #
    def detect_time(self, time_in_text):
        if not isinstance(time_in_text, str):
            return time_in_text
        #
        src = time_in_text.lower()
        #
        if src == 'now':
            return True, dict(human_time='Now', time=datetime.now())
        #
        ok, result = self.detect_today_or_tomorrow_HH_am_pm(src)
        if ok:
            return ok, result
        #
        ok, result = self.detect_today_or_tomorrow_HH_MM_am_pm(src)
        if ok:
            return ok, result
        #
        ok, result = self.detect_yyyy_mm_dd_HH_MM_am_pm(src)
        if ok:
            return ok, result
        #
        return False, dict(human_time=time_in_text, time=None)
    #
    #
    def detect_today_or_tomorrow_HH_am_pm(self, tit):
        mo = re.match(r'(today|tomorrow),?\s*([0-9]{1,2})(am|pm)', tit)
        if mo:
            period = mo.group(3)
            #
            hh_int = int(mo.group(2))
            #
            day = mo.group(1)
            #
            if hh_int < 24:
                mytime = self.set_today_or_tomorrow_time(hh_int, period=period, day=day)
                return True, dict(human_time=mytime.strftime(day.capitalize() + ', %I') + period, time=mytime)
        return False, None
    #
    #
    def detect_today_or_tomorrow_HH_MM_am_pm(self, tit):
        mo = re.match(r'(today|tomorrow),?\s*([0-9]{1,2}):([0-9]{1,2})(am|pm)', tit)
        if mo:
            period = mo.group(4)
            #
            mm_int = int(mo.group(3))
            #
            hh_int = int(mo.group(2))
            #
            day = mo.group(1)
            #
            if hh_int < 24 and mm_int < 60:
                mytime = self.set_today_or_tomorrow_time(hh_int, minutes=mm_int, period=period, day=day)
                return True, dict(human_time=mytime.strftime(day.capitalize() + ', %I:%M') + period, time=mytime)
        return False, None
    #
    #
    def detect_yyyy_mm_dd_HH_MM_am_pm(self, tit):
        mo = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4}),?\s*([0-9]{1,2}):([0-9]{1,2})(am|pm)', tit)
        if mo:
            #
            day = int(mo.group(1))
            #
            month = int(mo.group(2))
            #
            year = int(mo.group(3))
            #
            hh_int = int(mo.group(4))
            #
            mm_int = int(mo.group(5))
            #
            period = mo.group(6)
            #
            if hh_int < 24 and mm_int < 60:
                try:
                    mytime = datetime(year=year, month=month, day=day,
                            hour=hh_int, minute=mm_int, tzinfo=pytz.timezone(self.__timezone))
                    return True, dict(human_time=mytime.strftime('%d/%m/%Y, %I:%M') + period, time=mytime)
                except ValueError as err:
                    return False, dict(human_time=tit, error=err)
        return False, None
    #
    #
    def set_today_or_tomorrow_time(self, hours, minutes=0, period=None, day='today'):
        if period == 'pm' and hours < 12:
            hours = hours + 12
        #
        if day == 'tomorrow':
            begin = pendulum.tomorrow(self.__timezone)
        else:
            begin = pendulum.today(self.__timezone)
        #
        return begin + timedelta(hours=hours,minutes=minutes)
