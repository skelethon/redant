#!/usr/bin/env python3

import unittest
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../..', 'src'))

from redant.engine import Descriptor

class DescriptorTest(unittest.TestCase):

    def setUp(self):
        pass

    def test_ok(self):
        self.assertTrue(True)
