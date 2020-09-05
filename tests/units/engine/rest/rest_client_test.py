#!/usr/bin/env python3

import unittest

from redant.engine.rest import RestClient

class RestClient_constructor_test(unittest.TestCase):
    #
    def setUp(self):
        pass
    #
    def test_raise_TypeError(self):
        with self.assertRaises(TypeError) as context:
            er = ExampleRestClient()


class ExampleRestClient(RestClient):
    pass
