#!/usr/bin/env python

import logging
import os

from prometheus_flask_exporter import PrometheusMetrics
from prometheus_flask_exporter.multiprocess import UWsgiPrometheusMetrics

from redant.utils.logging import getLogger
from redant.utils.wsgi_util import IS_UWSGI_SUPPORTED, IS_UWSGI_IN_LAZY_APPS

LOG = getLogger(__name__)

metrics = PrometheusMetrics.for_app_factory()

if IS_UWSGI_SUPPORTED:
    metrics = UWsgiPrometheusMetrics.for_app_factory()

def start_metrics_server():
    if IS_UWSGI_IN_LAZY_APPS:
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug('Start metrics server in UWSGI [lazy-apps mode]')
        metrics.register_endpoint('/metrics')
        return
    if IS_UWSGI_SUPPORTED:
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug('Start metrics server in UWSGI')
        metrics.start_http_server(int(os.getenv('METRICS_PORT')))
        return

def metrics_hook(app):
    metrics.init_app(app)
    with app.app_context():
        start_metrics_server()
