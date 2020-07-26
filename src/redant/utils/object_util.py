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
        return o.__str__()
    return o

def jsonify(obj, field_names=[]):
    return json.dumps(pick_object_fields(obj, field_names), default = json_converter, ensure_ascii=False)
