"""
Flask extension singletons.
Import these throughout the app; they are bound to the app in factory.py.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from celery import Celery

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
limiter = Limiter(key_func=get_remote_address)

# Celery is initialised without an app; factory.py calls _configure_celery().
celery = Celery()


def _configure_celery(app):
    """Push Flask app config into the Celery instance and make tasks
    execute inside an app context."""
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        task_serializer=app.config["CELERY_TASK_SERIALIZER"],
        result_serializer=app.config["CELERY_RESULT_SERIALIZER"],
        accept_content=app.config["CELERY_ACCEPT_CONTENT"],
        task_track_started=app.config["CELERY_TASK_TRACK_STARTED"],
        task_acks_late=app.config["CELERY_TASK_ACKS_LATE"],
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery