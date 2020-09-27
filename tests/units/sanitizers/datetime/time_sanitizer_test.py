#!/usr/bin/env python3

import unittest

from datetime import datetime
from redant.sanitizers.datetime import TimeSanitizer
from redant.utils.object_util import json_dumps

class TimeSanitizer_detect_time_test(unittest.TestCase):
    #
    def test_ok(self):
        s = TimeSanitizer(timezone='Asia/Saigon')
        #
        ok, o = s.detect_time('Now')
        self.assertEqual(o['human_time'], 'Now')
        self.assertIsInstance(o['time'], datetime)
        #
        ok, o = s.detect_time('now')
        self.assertEqual(o['human_time'], 'Now')
        self.assertIsInstance(o['time'], datetime)
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
        pass
