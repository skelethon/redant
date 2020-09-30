#!/usr/bin/env python3

import unittest
from unittest.mock import patch, Mock

from datetime import datetime
from redant.sanitizers.datetime import TimeSanitizer
from redant.utils.object_util import json_dumps

class TimeSanitizer_detect_time_test(unittest.TestCase):
    #
    def print_only(self):
        s = TimeSanitizer(timezone='Asia/Kuala_Lumpur')
        #
        ok, o = s.detect_time('Now')
        print(json_dumps(o))
        #
        ok, o = s.detect_time('Today, 11am')
        print(json_dumps(o))
        #
        ok, o = s.detect_time('Today, 5:32pm')
        print(json_dumps(o))
        #
        ok, o = s.detect_time('TOMORROW, 09:3pm')
        print(json_dumps(o))
        #
        ok, o = s.detect_time('1/12/2020, 09:3pm')
        print(json_dumps(o))
        #
        ok, o = s.detect_time('10/12/2020, 7pm')
        print(json_dumps(o))
    #
    #
    def test__detect_now_ok(self):
        s = TimeSanitizer(timezone='Asia/Saigon')
        with patch('redant.sanitizers.datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2020, 10, 1, hour=9, minute=15, second=0, tzinfo=None)
            ok, o = s.detect_time('Now')
            self.assertTrue(ok)
            self.assertEqual(o['human_time'], 'Now')
            self.assertEqual(print_datetime(o['time']), '2020-10-01T09:15:00.000000+0700')
            self.assertTrue(mock_datetime.now.has_been_called())
    #
    #
    
    #
    #
    def test__detect_yyyy_mm_dd_HH_MM_am_pm__ok1(self):
        s = TimeSanitizer(timezone='Asia/Kuala_Lumpur')
        ok, o = s.detect_time('10/12/2020, 7pm')
        self.assertTrue(ok)
        self.assertEqual(o['human_time'], '10/12/2020, 07:00pm')
        self.assertEqual(print_datetime(o['time']), '2020-12-10T19:00:00.000000+0800')
    #
    def test__detect_yyyy_mm_dd_HH_MM_am_pm__ok2(self):
        s = TimeSanitizer(timezone='Asia/Hong_Kong')
        ok, o = s.detect_time('10/12/2020, 21:48pm')
        self.assertTrue(ok)
        self.assertEqual(o['human_time'], '10/12/2020, 09:48pm')
        self.assertEqual(print_datetime(o['time']), '2020-12-10T21:48:00.000000+0800')


def print_datetime(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f%z')
