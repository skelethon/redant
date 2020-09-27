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
    def detect_today_or_tomorrow_HH_MM_am_pm(self, tit):
        mo = re.match(r'(?P<day>today|tomorrow),?\s*(?P<hour>[0-9]{1,2})(:(?P<minute>[0-9]{1,2}))?(?P<period>am|pm)', tit)
        if mo:
            day = mo.group('day')
            #
            hh_int = int(mo.group('hour'))
            #
            mm_str = mo.group('minute')
            if mm_str is not None:
                mm_int = int(mm_str)
            else:
                mm_int = 0
            #
            period = mo.group('period')
            #
            if hh_int < 24 and mm_int < 60:
                mytime = self.set_today_or_tomorrow_time(hh_int, minutes=mm_int, period=period, day=day)
                return True, dict(human_time=mytime.strftime(day.capitalize() + ', %I:%M') + period, time=mytime)
        return False, None
    #
    #
    def detect_yyyy_mm_dd_HH_MM_am_pm(self, tit):
        mo = re.match(r'(?P<day>\d{1,2})/(?P<month>\d{1,2})/(?P<year>\d{4}),?\s*(?P<hour>[0-9]{1,2})(:(?P<minute>[0-9]{1,2}))?(?P<period>am|pm)', tit)
        if mo:
            #
            day = int(mo.group('day'))
            #
            month = int(mo.group('month'))
            #
            year = int(mo.group('year'))
            #
            hh_int = int(mo.group('hour'))
            #
            mm_str = mo.group('minute')
            if mm_str is not None:
                mm_int = int(mm_str)
            else:
                mm_int = 0
            #
            period = mo.group('period')
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
