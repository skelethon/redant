#!/usr/bin/env python

def removePrefix(prefix, line):
    if line.startswith(prefix):
        return line[len(prefix):]
    return line
