"""
Celery tasks for asynchronous scanning.
"""
import logging

from azure.core.exceptions import ServiceRequestError, ServiceResponseError
from botocore.exceptions import (
    ConnectTimeoutError,
    ConnectionClosedError,
    EndpointConnectionError,
    ReadTimeoutError,
)
from config.settings import BaseConfig
from app.core.extensions import celery, db
from app.models.scan import ScanJob
from app.services.scanner.scan_orchestrator import run_scan
from google.api_core.exceptions import (
    DeadlineExceeded,
    InternalServerError,
    ResourceExhausted,
    ServiceUnavailable,
    TooManyRequests,
)

logger = logging.getLogger(__name__)


@celery.task(
    bind=True,
    name="securevault.tasks.run_scan",
    autoretry_for=(
        TimeoutError,
        ConnectTimeoutError,
        ConnectionClosedError,
        EndpointConnectionError,
        ReadTimeoutError,
        ServiceRequestError,
        ServiceResponseError,
        DeadlineExceeded,
        InternalServerError,
        ResourceExhausted,
        ServiceUnavailable,
        TooManyRequests,
    ),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=5,
    soft_time_limit=BaseConfig.CELERY_TASK_SOFT_TIME_LIMIT,
    time_limit=BaseConfig.CELERY_TASK_TIME_LIMIT,
    acks_late=True,
    reject_on_worker_lost=True,
)
def run_scan_task(self, job_id: int) -> dict:
    """
    Celery entry point for a repository scan.

    Args:
        job_id: Primary key of the ScanJob row.

    Returns:
        Dict with job_id and final status.
    """
    logger.info("Celery task %s starting for job_id=%d", self.request.id, job_id)

    try:
        run_scan(job_id)
    except Exception as exc:
        logger.error(
            "Task %s failed (attempt %d/%d); exception_type=%s",
            self.request.id,
            self.request.retries + 1,
            self.max_retries + 1,
            type(exc).__name__,
        )
        raise
    job = db.session.get(ScanJob, job_id)
    return {
        "job_id": job_id,
        "status": job.status.value if job else "missing",
    }