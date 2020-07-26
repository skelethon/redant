#!/usr/bin/env python

import uuid

def generate_uuid():
    return str(uuid.uuid4())

def removePrefix(prefix, line):
    if line.startswith(prefix):
        return line[len(prefix):]
    return line
