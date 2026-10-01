"""
Flask extension singletons.
Import these throughout the app; they are bound to the app in factory.py.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import get_jwt_identity
from celery import Celery
from celery.signals import worker_process_shutdown
from flask import has_request_context
import logging


def _rate_limit_identity():
    if has_request_context():
        try:
            user_id = get_jwt_identity()
        except RuntimeError:
            user_id = None
        if user_id is not None:
            return f"user:{user_id}"
    return get_remote_address()

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
limiter = Limiter(key_func=_rate_limit_identity)
logger = logging.getLogger(__name__)

# Celery is initialised without an app; factory.py calls _configure_celery().
celery = Celery()


def _configure_celery(app):
    """Push Flask app config into the Celery instance and make tasks
    execute inside an app context."""
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        broker_connection_timeout=app.config["CELERY_BROKER_CONNECTION_TIMEOUT"],
        broker_transport_options={
            "socket_connect_timeout": app.config["CELERY_BROKER_CONNECTION_TIMEOUT"],
            "socket_timeout": app.config["CELERY_BROKER_CONNECTION_TIMEOUT"],
        },
        task_publish_retry=True,
        task_publish_retry_policy={
            "max_retries": app.config["CELERY_TASK_PUBLISH_MAX_RETRIES"],
            "interval_start": 0.1,
            "interval_step": 0.1,
            "interval_max": 0.2,
        },
        task_serializer=app.config["CELERY_TASK_SERIALIZER"],
        result_serializer=app.config["CELERY_RESULT_SERIALIZER"],
        accept_content=app.config["CELERY_ACCEPT_CONTENT"],
        task_track_started=app.config["CELERY_TASK_TRACK_STARTED"],
        task_acks_late=app.config["CELERY_TASK_ACKS_LATE"],
        task_soft_time_limit=app.config["CELERY_TASK_SOFT_TIME_LIMIT"],
        task_time_limit=app.config["CELERY_TASK_TIME_LIMIT"],
        worker_cancel_long_running_tasks_on_connection_loss=True,
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    def cleanup_worker_resources(**_kwargs):
        try:
            with app.app_context():
                db.session.remove()
                db.engine.dispose()
        except Exception as exc:
            logger.error(
                "Celery worker shutdown cleanup failed; exception_type=%s",
                type(exc).__name__,
            )

    worker_process_shutdown.connect(
        cleanup_worker_resources,
        weak=False,
        dispatch_uid=f"securevault-worker-shutdown-{id(app)}",
    )
    return celery