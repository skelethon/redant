#!/usr/bin/env python

import importlib

def checkModule(name, package=None):
  try:
    importlib.import_module(name, package)
    return True
  except ModuleNotFoundError as not_found_err:
    return False
  # spam_spec = importlib.find_loader(name, package)
  # return spam_spec is not None

def importModule(name, package=None):
  try:
    return importlib.import_module(name, package)
  except ModuleNotFoundError as not_found_err:
    raise not_found_err
