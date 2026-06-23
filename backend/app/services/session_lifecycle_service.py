from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from collections.abc import Callable, Iterator
from contextlib import contextmanager

from app.settings import settings


logger = logging.getLogger(__name__)


def _delete_langgraph_thread(session_id: str) -> None:
    from app.services.agent_graph_service import app as agent_app

    if agent_app.checkpointer is not None:
        agent_app.checkpointer.delete_thread(session_id)


class SessionLifecycleService:
    """Process-local activity tracking and opportunistic session cleanup."""

    def __init__(
        self,
        *,
        delete_thread: Callable[[str], None],
        inactivity_ttl_seconds: int,
        cleanup_interval_seconds: int,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if inactivity_ttl_seconds <= 0:
            raise ValueError("inactivity_ttl_seconds must be greater than zero")
        if cleanup_interval_seconds < 0:
            raise ValueError("cleanup_interval_seconds cannot be negative")

        self._delete_thread = delete_thread
        self._inactivity_ttl_seconds = inactivity_ttl_seconds
        self._cleanup_interval_seconds = cleanup_interval_seconds
        self._clock = clock or time.monotonic
        self._lock = threading.Lock()
        self._last_seen: dict[str, float] = {}
        self._active_requests: dict[str, int] = defaultdict(int)
        self._pending_deletions: set[str] = set()
        self._last_cleanup: float | None = None

    @contextmanager
    def activity(self, session_id: str) -> Iterator[None]:
        self._begin_activity(session_id)
        try:
            yield
        finally:
            self._end_activity(session_id)

    def delete_session(self, session_id: str) -> None:
        """Delete immediately, or defer deletion until active requests finish."""
        with self._lock:
            if session_id not in self._last_seen:
                return
            if self._active_requests[session_id] > 0:
                self._pending_deletions.add(session_id)
                return
            self._delete_tracked_session_locked(session_id, raise_on_error=True)

    def _begin_activity(self, session_id: str) -> None:
        with self._lock:
            now = self._clock()
            self._last_seen[session_id] = now
            self._active_requests[session_id] += 1
            self._cleanup_if_due_locked(now)

    def _end_activity(self, session_id: str) -> None:
        with self._lock:
            remaining = self._active_requests[session_id] - 1
            if remaining > 0:
                self._active_requests[session_id] = remaining
                return

            self._active_requests.pop(session_id, None)
            if session_id in self._pending_deletions:
                self._delete_tracked_session_locked(session_id, raise_on_error=False)
                return
            self._last_seen[session_id] = self._clock()

    def _cleanup_if_due_locked(self, now: float) -> None:
        if (
            self._last_cleanup is not None
            and now - self._last_cleanup < self._cleanup_interval_seconds
        ):
            return
        self._last_cleanup = now

        expired_session_ids = [
            session_id
            for session_id, last_seen in self._last_seen.items()
            if self._active_requests.get(session_id, 0) == 0
            and now - last_seen >= self._inactivity_ttl_seconds
        ]
        pending_session_ids = [
            session_id
            for session_id in self._pending_deletions
            if self._active_requests.get(session_id, 0) == 0
        ]

        for session_id in set(expired_session_ids + pending_session_ids):
            self._delete_tracked_session_locked(session_id, raise_on_error=False)

    def _delete_tracked_session_locked(
        self,
        session_id: str,
        *,
        raise_on_error: bool,
    ) -> None:
        try:
            self._delete_thread(session_id)
        except Exception:
            if raise_on_error:
                raise
            logger.exception("Failed to delete in-memory session %s", session_id)
            return

        self._last_seen.pop(session_id, None)
        self._active_requests.pop(session_id, None)
        self._pending_deletions.discard(session_id)
        logger.info("Deleted in-memory session %s", session_id)


session_lifecycle = SessionLifecycleService(
    delete_thread=_delete_langgraph_thread,
    inactivity_ttl_seconds=settings.SESSIONS.INACTIVITY_TTL_SECONDS,
    cleanup_interval_seconds=settings.SESSIONS.CLEANUP_INTERVAL_SECONDS,
)
