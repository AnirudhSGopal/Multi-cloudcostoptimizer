from app.core.extensions import celery
from app.core.factory import create_app
from app.tasks.scan_tasks import run_scan_task


def test_scan_task_retries_transient_failures_with_jitter_and_time_limits():
    assert run_scan_task.autoretry_for
    assert run_scan_task.retry_backoff is True
    assert run_scan_task.retry_jitter is True
    assert run_scan_task.max_retries == 5
    assert run_scan_task.soft_time_limit < run_scan_task.time_limit


def test_celery_publish_fails_fast_when_broker_is_unavailable():
    app = create_app("testing")

    assert app.config["CELERY_BROKER_CONNECTION_TIMEOUT"] <= 10
    assert celery.conf.broker_connection_timeout == app.config[
        "CELERY_BROKER_CONNECTION_TIMEOUT"
    ]
    assert celery.conf.broker_transport_options["socket_connect_timeout"] == app.config[
        "CELERY_BROKER_CONNECTION_TIMEOUT"
    ]
    assert celery.conf.broker_transport_options["socket_timeout"] == app.config[
        "CELERY_BROKER_CONNECTION_TIMEOUT"
    ]
    assert celery.conf.task_publish_retry_policy["max_retries"] == app.config[
        "CELERY_TASK_PUBLISH_MAX_RETRIES"
    ]
