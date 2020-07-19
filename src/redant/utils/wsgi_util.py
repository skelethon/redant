#!/usr/bin/env python

from redant.utils.module_util import checkModule, importModule

IS_UWSGI_SUPPORTED = checkModule('uwsgi')

def getUwsgiMasterPid():
    if not IS_UWSGI_SUPPORTED:
        return None
    import uwsgi
    return uwsgi.masterpid()

def isUwsgiMaster():
    if not IS_UWSGI_SUPPORTED:
        return False
    import os, uwsgi
    return os.getpid() == uwsgi.masterpid()

def isUwsgiLazyApps():
    if not IS_UWSGI_SUPPORTED:
        return False
    import uwsgi
    return 'lazy-apps' in uwsgi.opt and uwsgi.opt['lazy-apps']

IS_UWSGI_IN_LAZY_APPS = isUwsgiLazyApps()
