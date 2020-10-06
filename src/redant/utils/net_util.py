#!/usr/bin/env python3

from urllib.parse import urlparse, urlunparse, ParseResult

def url_build(scheme='https', host='', path='', params='', query='', fragment=''):
    parts = ParseResult(scheme=scheme, netloc=host, path=path, params=params, query=query, fragment=fragment)
    return urlunparse(parts)
