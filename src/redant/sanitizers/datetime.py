#!/usr/bin/env python

import re
import pytz

from datetime import datetime, timedelta, tzinfo
from redant.errors import InvalidTimeZoneError

class TimeSanitizer(object):
    #
    def __init__(self, timezone=None):
        if isinstance(timezone, str):
            self.__timezone = pytz.timezone(timezone)
            return
        if timezone is not None and not isinstance(timezone, tzinfo):
            raise InvalidTimeZoneError('Invalid timezone: {}'.format(str(timezone)))
        self.__timezone = timezone
    #
    #
    def detect_time(self, time_in_text, timezone=None):
        #
        timezone = self.__get_timezone(timezone)
        #
        if not isinstance(time_in_text, str):
            return time_in_text
        #
        src = time_in_text.lower()
        #
        if src == 'now':
            return True, dict(human_time='Now', time=datetime_now(timezone))
        #
        ok, result = self.detect_today_or_tomorrow_HH_MM_am_pm(src, timezone)
        if ok and result is not None:
            return ok, result
        #
        ok, result = self.detect_yyyy_mm_dd_HH_MM_am_pm(src, timezone)
        if ok and result is not None:
            return ok, result
        #
        return False, None
    #
    #
    def detect_today_or_tomorrow_HH_MM_am_pm(self, tit, timezone):
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
                try:
                    mytime = self.set_today_or_tomorrow_time(hh_int, minute=mm_int, period=period, day=day, timezone=timezone)
                    return True, dict(human_time=mytime.strftime(day.capitalize() + ', %I:%M') + period, time=mytime)
                except Exception as err:
                    return False, dict(human_time=tit, error=err)
        return False, None
    #
    #
    def detect_yyyy_mm_dd_HH_MM_am_pm(self, tit, timezone):
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
            if period == 'pm' and hh_int < 12:
                hh_int = hh_int + 12
            #
            if hh_int < 24 and mm_int < 60:
                try:
                    mytime = datetime_now(timezone).replace(year=year, month=month, day=day,
                            hour=hh_int, minute=mm_int, second=0, microsecond=0)
                    return True, dict(human_time=mytime.strftime('%d/%m/%Y, %I:%M') + period, time=mytime)
                except ValueError as err:
                    return False, dict(human_time=tit, error=err)
        return False, None
    #
    #
    def set_today_or_tomorrow_time(self, hour=0, minute=0, period=None, day='today', timezone=None):
        if period == 'pm' and hour < 12:
            hour = hour + 12
        #
        if day == 'tomorrow':
            return self.__today_at(timezone, hour, minute) + timedelta(days=1)
        #
        return self.__today_at(timezone, hour, minute)
    #
    #
    def __get_timezone(self, timezone=None):
        if timezone is None:
            return self.__timezone
        if isinstance(timezone, str):
            return pytz.timezone(timezone)
        return timezone
    #
    #
    def __today_at(self, timezone, hour=0, minute=0, second=0):
        return datetime_now(timezone).replace(hour=hour, minute=minute, second=second, microsecond=0)


def datetime_now(timezone):
    return datetime.now().astimezone(timezone)
