from datadog import initialize
import os
from datadog.threadstats import ThreadStats

DD_API_KEY = os.environ.get("DD_API_KEY")

stats = None


def init_metrics():
    global stats
    if DD_API_KEY:
        options = {
            "api_key": DD_API_KEY,
        }
        initialize(**options)
        stats = ThreadStats()
        stats.start()  # Creates a worker thread used to submit metrics.


def stats_gauge(metric_name, value):
    if DD_API_KEY:
        stats.gauge(metric_name, value)


def stats_count(metric_name, value=1):
    if DD_API_KEY:
        stats.increment(metric_name, value)
