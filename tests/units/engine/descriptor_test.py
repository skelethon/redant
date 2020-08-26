#!/usr/bin/env python3

import unittest
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../..', 'src'))

from redant.engine import Descriptor

class Descriptor_enhanceRules_test(unittest.TestCase):

    def setUp(self):
        pass

    def test_ok(self):
        rules = [
            {
                'trigger': 'next',
                'source': 'anything',
                'dest': 'welcome',
                'after': ['transition_after']
            },
            {
                'trigger': 'next',
                'source': 'welcome',
                'dest': 'waiting_for_name',
                'before': ['transition_before'],
                'after': ['save_dialog', 'transition_after']
            },
            {
                'trigger': 'next',
                'source': 'waiting_for_name',
                'dest': 'waiting_for_age'
            }
        ]
        #
        expected_rules = [
            {
                'trigger': 'next',
                'source': 'anything',
                'dest': 'welcome',
                'after': ['save_dialog', 'transition_after']
            },
            {
                'trigger': 'next',
                'source': 'welcome',
                'dest': 'waiting_for_name',
                'before': ['transition_before'],
                'after': ['save_dialog', 'transition_after']
            },
            {
                'trigger': 'next',
                'source': 'waiting_for_name',
                'dest': 'waiting_for_age',
                'after': ['save_dialog']
            }
        ]
        #
        new_rules = Descriptor.enhanceRules(rules)
        #
        self.assertListEqual(new_rules, expected_rules)
