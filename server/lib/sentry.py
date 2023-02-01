import os
import sentry_sdk


def init_sentry():
    if not os.environ["SENTRY_DSN"]:
        return
    if not os.environ["ENV"] in ['prod', 'staging']:
        return
    sentry_sdk.init(
        dsn=os.environ["SENTRY_DSN"],
        environment=os.environ["ENV"],
        traces_sample_rate=1.0,  # adjust the sample rate in production as needed
    )
