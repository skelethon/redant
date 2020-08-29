#!/usr/bin/env python3

import unittest

from redant.engine import Descriptor

class Descriptor_enhanceRules_test(unittest.TestCase):

    def setUp(self):
        pass

    def test_ok(self):
        rules = [
            {
                'source': 'anything',
                'target': 'welcome'
            },
            {
                'source': 'welcome',
                'target': 'waiting_for_name',
                'before': ['transition_before'],
                'after': ['save_dialog', 'transition_after']
            },
            {
                'trigger': 'action',
                'source': 'waiting_for_name',
                'target': 'waiting_for_age',
                'after': ['commit']
            }
        ]
        #
        expected_rules = [
            {
                'trigger': 'next',
                'source': 'anything',
                'dest': 'welcome',
                'before': ['transition_before'],
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
                'trigger': 'action',
                'source': 'waiting_for_name',
                'dest': 'waiting_for_age',
                'before': ['transition_before'],
                'after': ['save_dialog', 'commit', 'transition_after']
            }
        ]
        #
        new_rules = Descriptor.enhanceRules(rules)
        #
        self.assertListEqual(new_rules, expected_rules)
