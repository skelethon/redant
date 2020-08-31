#!/usr/bin/env python3

import unittest

from redant.utils.function_util import call_function

class call_function_test(unittest.TestCase):

    def setUp(self):
        pass

    def test_ok(self):
        e = Example1()
        self.assertEqual(call_function('f1', e, 10, 20), 30)
        self.assertEqual(call_function('f1', e, 10, b=20), 30)
        self.assertEqual(call_function('f1', e, b=10, a=20), 30)
        self.assertEqual(call_function('f2', e), 100)

class Example1(object):
    def f1(self, a, b=50):
        return a + b
    def f2(self):
        return 100
