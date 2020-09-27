#!/usr/bin/env python3

import unittest

from redant.utils.net_util import url_build

class url_build_test(unittest.TestCase):

    def setUp(self):
        pass

    def test_ok(self):
        self.assertEqual(url_build(hostname='example.com'), 'https://example.com')
        self.assertEqual(url_build(hostname='example.com', path='/'), 'https://example.com/')
