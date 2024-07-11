from datadog import initialize
import socket
import os
from datadog.threadstats import ThreadStats

DD_API_KEY = os.environ.get("DD_API_KEY")

stats = None
# Get the host name
host_name = socket.gethostname()


def init_metrics():
    global stats
    if DD_API_KEY:
        options = {
            "api_key": DD_API_KEY,
        }
        initialize(**options)
        stats = ThreadStats()
        stats.start()  # Creates a worker thread used to submit metrics.


def stats_gauge(metric_name, value, tags=[]):
    if DD_API_KEY:
        tags.append(f"host:{host_name}")
        stats.gauge(metric_name, value, tags=tags)


def stats_count(metric_name, value=1, tags=[]):
    if DD_API_KEY:
        tags.append(f"host:{host_name}")
        stats.increment(metric_name, value, tags=tags)
