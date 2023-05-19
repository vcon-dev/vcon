import os
from lib.error_trackers.sentry import init_sentry


def init_error_tracker():
    if os.environ.get("SENTRY_DSN"):
        init_sentry()