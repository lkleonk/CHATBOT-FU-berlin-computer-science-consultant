from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes import session_router
from app.services.session_lifecycle_service import SessionLifecycleService


def _lifecycle(clock, deleted, *, ttl=86_400, cleanup_interval=300):
    return SessionLifecycleService(
        delete_thread=deleted.append,
        inactivity_ttl_seconds=ttl,
        cleanup_interval_seconds=cleanup_interval,
        clock=lambda: clock[0],
    )


def test_inactive_session_is_deleted_during_later_activity():
    clock = [0.0]
    deleted = []
    lifecycle = _lifecycle(clock, deleted)

    with lifecycle.activity("old-session"):
        pass

    clock[0] = 86_401.0
    with lifecycle.activity("current-session"):
        assert deleted == ["old-session"]


def test_current_session_is_touched_before_cleanup():
    clock = [0.0]
    deleted = []
    lifecycle = _lifecycle(clock, deleted)

    with lifecycle.activity("same-session"):
        pass

    clock[0] = 86_401.0
    with lifecycle.activity("same-session"):
        pass

    assert deleted == []


def test_cleanup_only_scans_at_the_configured_interval():
    clock = [0.0]
    deleted = []
    lifecycle = _lifecycle(clock, deleted, ttl=10, cleanup_interval=5)

    with lifecycle.activity("old-session"):
        pass

    clock[0] = 11.0
    with lifecycle.activity("current-session"):
        pass
    assert deleted == ["old-session"]

    clock[0] = 12.0
    with lifecycle.activity("another-session"):
        pass
    assert deleted == ["old-session"]


def test_explicit_delete_waits_for_active_request_to_finish():
    clock = [0.0]
    deleted = []
    lifecycle = _lifecycle(clock, deleted)

    with lifecycle.activity("active-session"):
        lifecycle.delete_session("active-session")
        assert deleted == []

    assert deleted == ["active-session"]


def test_explicit_delete_of_unknown_session_is_idempotent():
    clock = [0.0]
    deleted = []
    lifecycle = _lifecycle(clock, deleted)

    lifecycle.delete_session("unknown-session")

    assert deleted == []


def test_delete_session_route_returns_204(monkeypatch):
    deleted = []

    class FakeSessionService:
        def delete_session(self, session_id):
            deleted.append(session_id)

    monkeypatch.setattr("app.routes.get_session_service", lambda: FakeSessionService())
    app = FastAPI()
    app.include_router(session_router)

    with TestClient(app) as client:
        response = client.delete("/api/sessions/session-123")

    assert response.status_code == 204
    assert response.content == b""
    assert deleted == ["session-123"]
