from flask import Flask

from app.services.cloud import gemini_guard


class FakeRedis:
    def __init__(self):
        self.values = {}

    def eval(self, script, key_count, *args):
        keys = args[:key_count]
        values = args[key_count:]
        if "global_count" in script:
            user_limit, global_limit, _expiry = map(int, values)
            user_count = int(self.values.get(keys[0], 0))
            global_count = int(self.values.get(keys[1], 0))
            if user_count >= user_limit or global_count >= global_limit:
                return 0
            self.values[keys[0]] = user_count + 1
            self.values[keys[1]] = global_count + 1
            return 1

        failures, _cooldown = map(int, values)
        self.values[keys[0]] = int(self.values.get(keys[0], 0)) + 1
        if self.values[keys[0]] >= failures:
            self.values["securevault:gemini:circuit:open"] = 1
        return self.values[keys[0]]

    def exists(self, key):
        return int(key in self.values)

    def delete(self, key):
        self.values.pop(key, None)


def test_gemini_call_quota_enforces_user_and_global_daily_caps(monkeypatch):
    app = Flask(__name__)
    app.config.update(GEMINI_DAILY_USER_QUOTA=1, GEMINI_DAILY_GLOBAL_CAP=2)
    store = FakeRedis()
    monkeypatch.setattr(gemini_guard, "_redis_client", lambda: store)

    with app.app_context():
        assert gemini_guard.reserve_gemini_call(10) is True
        assert gemini_guard.reserve_gemini_call(10) is False
        assert gemini_guard.reserve_gemini_call(11) is True
        assert gemini_guard.reserve_gemini_call(12) is False


def test_gemini_circuit_opens_after_configured_consecutive_failures(monkeypatch):
    app = Flask(__name__)
    app.config.update(
        GEMINI_CIRCUIT_BREAKER_FAILURES=2,
        GEMINI_CIRCUIT_BREAKER_RESET_SECONDS=60,
    )
    store = FakeRedis()
    monkeypatch.setattr(gemini_guard, "_redis_client", lambda: store)

    with app.app_context():
        assert gemini_guard.gemini_circuit_is_open() is False
        gemini_guard.record_gemini_failure()
        assert gemini_guard.gemini_circuit_is_open() is False
        gemini_guard.record_gemini_failure()
        assert gemini_guard.gemini_circuit_is_open() is True


def test_optimizer_uses_heuristics_when_circuit_is_open(monkeypatch):
    from app.services.cloud import optimizer

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_guard, "gemini_circuit_is_open", lambda: True)
    heuristic_recommendations = [{"id": "rule-based", "estimated_monthly_savings": 10}]

    result = optimizer._enhance_with_gemini(
        heuristic_recommendations,
        resources=[],
        cost_data=[],
        user_id=10,
    )

    assert result == heuristic_recommendations
