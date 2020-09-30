#!/usr/bin/env python

import datetime
import json

def pick_object_fields(obj, field_names=[]):
  if len(field_names) == 0:
    return obj
  if isinstance(obj, dict):
    return {k: v for k, v in obj.items() if k in field_names}
  if isinstance(obj, object):
    output = dict()
    for field_name in field_names:
      if hasattr(obj, field_name):
        output[field_name] = getattr(obj, field_name)
    return output

def json_converter(o):
    if isinstance(o, datetime.datetime):
        return o.strftime('%Y-%m-%dT%H:%M:%S.%f%z')
    return o

def json_dumps(obj, field_names=[]):
    if isinstance(obj, str):
        return obj
    return json.dumps(pick_object_fields(obj, field_names), default = json_converter, ensure_ascii=False)

def json_loads(data):
    if not isinstance(data, str):
        return data, None
    try:
        json_dict = json.loads(data)
        return json_dict, None
    except Exception as exception:
        return None, exception
