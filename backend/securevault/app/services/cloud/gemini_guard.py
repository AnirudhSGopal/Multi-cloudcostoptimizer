"""Shared Redis-backed budget and circuit-breaker controls for Gemini calls."""
import logging
from datetime import datetime, timedelta, timezone

import redis
from flask import current_app, has_app_context

logger = logging.getLogger(__name__)

_DAILY_QUOTA_SCRIPT = """
local user_count = tonumber(redis.call('GET', KEYS[1]) or '0')
local global_count = tonumber(redis.call('GET', KEYS[2]) or '0')
if user_count >= tonumber(ARGV[1]) or global_count >= tonumber(ARGV[2]) then
    return 0
end
if redis.call('INCR', KEYS[1]) == 1 then redis.call('EXPIRE', KEYS[1], ARGV[3]) end
if redis.call('INCR', KEYS[2]) == 1 then redis.call('EXPIRE', KEYS[2], ARGV[3]) end
return 1
"""

_FAILURE_SCRIPT = """
local failures = redis.call('INCR', KEYS[1])
if failures == 1 then redis.call('EXPIRE', KEYS[1], ARGV[2]) end
if failures >= tonumber(ARGV[1]) then
    redis.call('SET', KEYS[2], '1', 'EX', ARGV[2])
end
return failures
"""


def _redis_client():
    if not has_app_context():
        raise RuntimeError("Gemini budget requires an application context")

    client = current_app.extensions.get("gemini_budget_redis")
    if client is None:
        redis_url = current_app.config.get("CELERY_BROKER_URL")
        if not redis_url:
            raise RuntimeError("Redis URL is not configured")
        client = redis.Redis.from_url(
            redis_url,
            socket_connect_timeout=1,
            socket_timeout=1,
            decode_responses=True,
        )
        current_app.extensions["gemini_budget_redis"] = client
    return client


def reserve_gemini_call(user_id) -> bool:
    """Atomically reserve one per-user and global Gemini call for the UTC day."""
    if user_id is None or not has_app_context():
        logger.warning("Gemini budget unavailable; using non-AI recommendations")
        return False

    now = datetime.now(timezone.utc)
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    expiry_seconds = max(1, int((tomorrow - now).total_seconds()))
    day = now.strftime("%Y%m%d")
    user_key = f"securevault:gemini:daily:user:{user_id}:{day}"
    global_key = f"securevault:gemini:daily:global:{day}"

    try:
        reserved = _redis_client().eval(
            _DAILY_QUOTA_SCRIPT,
            2,
            user_key,
            global_key,
            current_app.config.get("GEMINI_DAILY_USER_QUOTA", 25),
            current_app.config.get("GEMINI_DAILY_GLOBAL_CAP", 500),
            expiry_seconds,
        )
    except (redis.RedisError, RuntimeError, ValueError) as exc:
        logger.warning("Gemini budget unavailable (%s); using non-AI recommendations", type(exc).__name__)
        return False
    return bool(reserved)


def gemini_circuit_is_open() -> bool:
    """Return true when repeated provider failures have opened the circuit."""
    try:
        return bool(_redis_client().exists("securevault:gemini:circuit:open"))
    except (redis.RedisError, RuntimeError, ValueError) as exc:
        logger.warning("Gemini circuit state unavailable (%s); failing closed", type(exc).__name__)
        return True


def record_gemini_failure() -> None:
    """Record a failure and open the shared circuit for its cooldown interval."""
    try:
        _redis_client().eval(
            _FAILURE_SCRIPT,
            2,
            "securevault:gemini:circuit:failures",
            "securevault:gemini:circuit:open",
            current_app.config.get("GEMINI_CIRCUIT_BREAKER_FAILURES", 3),
            current_app.config.get("GEMINI_CIRCUIT_BREAKER_RESET_SECONDS", 300),
        )
    except (redis.RedisError, RuntimeError, ValueError) as exc:
        logger.warning("Could not update Gemini circuit state (%s)", type(exc).__name__)


def record_gemini_success() -> None:
    """Reset consecutive failures after a successful Gemini response."""
    try:
        _redis_client().delete("securevault:gemini:circuit:failures")
    except (redis.RedisError, RuntimeError, ValueError) as exc:
        logger.warning("Could not reset Gemini circuit state (%s)", type(exc).__name__)
