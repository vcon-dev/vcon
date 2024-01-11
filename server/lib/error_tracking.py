import os
import logging
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration


def init_sentry():
    sentry_sdk.init(
        dsn=os.environ["SENTRY_DSN"],
        environment=os.environ["ENV"],
        integrations=[
            LoggingIntegration(
                level=logging.INFO,  # Capture info and above as breadcrumbs
                event_level=logging.ERROR,
            )
        ],
        traces_sample_rate=0,  # adjust the sample rate in production as needed
    )


def init_error_tracker():
    if os.environ.get("SENTRY_DSN"):
        init_sentry()


def capture_exception(e):
    if os.environ.get("SENTRY_DSN"):
        sentry_sdk.capture_exception(e)
