import asyncio
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.services import model_service
from app.services.quota_service import DailyQuotaExceeded, InMemoryDailyQuota
from app.routes import session_router, usage_router
from app.settings import settings


def test_global_quota_rejects_actions_beyond_limit_across_clients():
    quota = InMemoryDailyQuota(
        global_action_limit=2,
        user_action_limit=10,
    )

    quota.consume_user_action("client-a")
    quota.consume_user_action("client-b")

    # Neither client is near their own limit; the service-wide budget is spent.
    with pytest.raises(DailyQuotaExceeded) as exc_info:
        quota.consume_user_action("client-c")

    assert exc_info.value.status_code == 429
    assert exc_info.value.detail["error_code"] == "daily_service_quota_exceeded"
    assert exc_info.value.detail["limit"] == 2
    assert exc_info.value.headers["X-RateLimit-Scope"] == "service_global"


def test_own_limit_is_reported_before_the_service_limit():
    quota = InMemoryDailyQuota(
        global_action_limit=1,
        user_action_limit=1,
    )
    quota.consume_user_action("client-a")

    # Both limits are now spent; the caller's own is the truthful reason.
    with pytest.raises(DailyQuotaExceeded) as exc_info:
        quota.consume_user_action("client-a")

    assert exc_info.value.detail["error_code"] == "daily_user_action_quota_exceeded"


def test_a_rejected_action_is_not_charged_to_either_counter():
    quota = InMemoryDailyQuota(
        global_action_limit=1,
        user_action_limit=5,
    )
    quota.consume_user_action("client-a")

    with pytest.raises(DailyQuotaExceeded):
        quota.consume_user_action("client-b")

    # client-b was refused, so it kept its whole allowance.
    assert quota.user_action_status("client-b")["used"] == 0
    assert quota.service_status()["used"] == 1


def test_service_status_reports_the_shared_budget():
    quota = InMemoryDailyQuota(
        global_action_limit=10,
        user_action_limit=5,
    )
    quota.consume_user_action("client-a")
    quota.consume_user_action("client-b")

    assert quota.service_status() == {"limit": 10, "used": 2, "remaining": 8}


def test_user_action_quota_is_scoped_by_client_id():
    quota = InMemoryDailyQuota(
        global_action_limit=10,
        user_action_limit=1,
    )

    quota.consume_user_action("client-a")
    quota.consume_user_action("client-b")

    with pytest.raises(DailyQuotaExceeded) as exc_info:
        quota.consume_user_action("client-a")

    assert exc_info.value.detail["error_code"] == "daily_user_action_quota_exceeded"
    assert exc_info.value.detail["limit"] == 1


def test_user_action_status_reports_remaining_and_reset():
    current_time = [datetime(2026, 6, 22, 12, 0, tzinfo=timezone.utc)]
    quota = InMemoryDailyQuota(
        global_action_limit=10,
        user_action_limit=3,
        clock=lambda: current_time[0],
    )

    consumed = quota.consume_user_action("client-a")
    status = quota.user_action_status("client-a")

    assert consumed["used"] == 1
    assert status["limit"] == 3
    assert status["used"] == 1
    assert status["remaining"] == 2
    assert status["reset_at"] == datetime(2026, 6, 23, tzinfo=timezone.utc)


def test_quotas_reset_on_the_next_utc_day():
    current_time = [datetime(2026, 6, 21, 23, 59, tzinfo=timezone.utc)]
    quota = InMemoryDailyQuota(
        global_action_limit=1,
        user_action_limit=1,
        clock=lambda: current_time[0],
    )
    quota.consume_user_action("client-a")

    current_time[0] = datetime(2026, 6, 22, 0, 0, tzinfo=timezone.utc)

    quota.consume_user_action("client-a")
    assert quota.service_status()["used"] == 1


def test_model_service_does_not_meter_provider_invocations(monkeypatch):
    """Quota is charged per user action in the routes, never per LLM call."""

    class FakeProvider:
        async def invoke(self, **kwargs):
            return {"content": "ok"}

    service = object.__new__(model_service.ModelService)
    service.provider = FakeProvider()

    result = asyncio.run(service.invoke(prompt="prompt", message="message"))

    assert result == {"content": "ok"}
    assert not hasattr(model_service, "daily_quota")


def test_user_action_route_returns_429_before_processing(monkeypatch):
    class RejectingQuota:
        def consume_user_action(self, client_id):
            raise DailyQuotaExceeded(
                error_code="daily_user_action_quota_exceeded",
                message="Daily action limit reached.",
                limit=100,
                reset_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
            )

    monkeypatch.setattr("app.routes.daily_quota", RejectingQuota())
    app = FastAPI()
    app.include_router(session_router)

    with TestClient(app) as client:
        response = client.post(
            "/api/sessions/any-session/message",
            json={"content": "How many LP?"},
        )

    assert response.status_code == 429
    assert response.json()["detail"]["error_code"] == "daily_user_action_quota_exceeded"
    assert response.headers["Retry-After"]
    assert response.headers["X-RateLimit-Remaining"] == "0"
    assert response.headers["X-RateLimit-Scope"] == "user_action"


def test_successful_user_action_returns_scoped_rate_limit_headers(monkeypatch):
    class FakeQuota:
        def consume_user_action(self, client_id):
            return {
                "limit": 100,
                "used": 90,
                "remaining": 10,
                "reset_at": datetime(2026, 6, 23, tzinfo=timezone.utc),
            }

    class FakeSessionService:
        async def process_message(self, session_id, content, tracing_enabled=True):
            return {
                "reply": "Answer",
                "message_type": "degree_question",
                "citations": [],
            }

    monkeypatch.setattr("app.routes.daily_quota", FakeQuota())
    monkeypatch.setattr("app.routes.get_session_service", lambda: FakeSessionService())
    app = FastAPI()
    app.include_router(session_router)

    with TestClient(app) as client:
        response = client.post(
            "/api/sessions/session-1/message",
            json={"content": "How many LP?"},
        )

    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"] == "100"
    assert response.headers["X-RateLimit-Remaining"] == "10"
    assert response.headers["X-RateLimit-Scope"] == "user_action"


def test_usage_route_returns_client_quota_and_retention(monkeypatch):
    class FakeQuota:
        def user_action_status(self, client_id):
            assert client_id == "testclient"
            return {
                "limit": 100,
                "used": 90,
                "remaining": 10,
                "reset_at": datetime(2026, 6, 23, tzinfo=timezone.utc),
            }

        def service_status(self):
            return {"limit": 200, "used": 150, "remaining": 50}

    monkeypatch.setattr("app.routes.daily_quota", FakeQuota())
    app = FastAPI()
    app.include_router(usage_router)

    with TestClient(app) as client:
        response = client.get("/api/usage")

    assert response.status_code == 200
    assert response.json()["remaining"] == 10
    assert response.json()["service"] == {"limit": 200, "used": 150, "remaining": 50}
    assert response.json()["session_inactivity_ttl_seconds"] == settings.SESSIONS.INACTIVITY_TTL_SECONDS
    assert response.json()["quota_scope"] == "client_ip"
