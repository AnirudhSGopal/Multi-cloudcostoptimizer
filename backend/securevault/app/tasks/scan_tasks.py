"""
Celery tasks for asynchronous scanning.
"""
import logging

from app.core.extensions import celery
from app.services.scanner.scan_orchestrator import run_scan

logger = logging.getLogger(__name__)


@celery.task(
    bind=True,
    name="securevault.tasks.run_scan",
    max_retries=3,
    default_retry_delay=30,   # seconds between retries
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
        return {"job_id": job_id, "status": "completed"}

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Task %s failed (attempt %d/%d): %s",
            self.request.id,
            self.request.retries + 1,
            self.max_retries + 1,
            exc,
        )
        # Retry with exponential back-off
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 30)