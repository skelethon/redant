#!/usr/bin/env python3

import unittest

from redant.engine.rest import RestClient

class RestClient_constructor_test(unittest.TestCase):

    def setUp(self):
        pass

    def test_ok(self):
        er = ExampleRestClient()
        pass


class ExampleRestClient(RestClient):
    pass
