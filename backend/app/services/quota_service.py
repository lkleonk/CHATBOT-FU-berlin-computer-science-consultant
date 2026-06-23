from __future__ import annotations

import math
import threading
from collections import defaultdict
from collections.abc import Callable
from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException

from app.settings import settings


class DailyQuotaExceeded(HTTPException):
    """HTTP 429 raised when an in-process daily quota is exhausted."""

    def __init__(self, *, error_code: str, message: str, limit: int, reset_at: datetime):
        retry_after = max(
            1,
            math.ceil((reset_at - datetime.now(timezone.utc)).total_seconds()),
        )
        super().__init__(
            status_code=429,
            detail={
                "error_code": error_code,
                "message": message,
                "limit": limit,
                "remaining": 0,
                "reset_at": reset_at.isoformat(),
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": reset_at.isoformat(),
                "X-RateLimit-Scope": (
                    "llm_global" if error_code == "daily_llm_quota_exceeded" else "user_action"
                ),
            },
        )


class InMemoryDailyQuota:
    """Process-local UTC-day counters for LLM calls and client actions."""

    def __init__(
        self,
        *,
        llm_invocation_limit: int,
        user_action_limit: int,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.llm_invocation_limit = llm_invocation_limit
        self.user_action_limit = user_action_limit
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._lock = threading.Lock()
        self._day: date | None = None
        self._llm_invocations = 0
        self._user_actions: dict[str, int] = defaultdict(int)

    def consume_llm_invocation(self) -> None:
        with self._lock:
            now = self._utc_now()
            self._roll_over_if_needed(now.date())
            if self._llm_invocations >= self.llm_invocation_limit:
                reset_at = self._next_reset(now.date())
                raise DailyQuotaExceeded(
                    error_code="daily_llm_quota_exceeded",
                    message="The daily LLM usage limit has been reached. Please try again tomorrow.",
                    limit=self.llm_invocation_limit,
                    reset_at=reset_at,
                )
            self._llm_invocations += 1

    def consume_user_action(self, client_id: str) -> dict[str, int | datetime]:
        with self._lock:
            now = self._utc_now()
            self._roll_over_if_needed(now.date())
            if self._user_actions[client_id] >= self.user_action_limit:
                reset_at = self._next_reset(now.date())
                raise DailyQuotaExceeded(
                    error_code="daily_user_action_quota_exceeded",
                    message="Your daily action limit has been reached. Please try again tomorrow.",
                    limit=self.user_action_limit,
                    reset_at=reset_at,
                )
            self._user_actions[client_id] += 1
            return self._user_action_status_locked(client_id, now.date())

    def user_action_status(self, client_id: str) -> dict[str, int | datetime]:
        with self._lock:
            now = self._utc_now()
            self._roll_over_if_needed(now.date())
            return self._user_action_status_locked(client_id, now.date())

    def _user_action_status_locked(
        self,
        client_id: str,
        current_day: date,
    ) -> dict[str, int | datetime]:
        used = self._user_actions[client_id]
        return {
            "limit": self.user_action_limit,
            "used": used,
            "remaining": max(0, self.user_action_limit - used),
            "reset_at": self._next_reset(current_day),
        }

    def _utc_now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None:
            return now.replace(tzinfo=timezone.utc)
        return now.astimezone(timezone.utc)

    def _roll_over_if_needed(self, current_day: date) -> None:
        if self._day == current_day:
            return
        self._day = current_day
        self._llm_invocations = 0
        self._user_actions.clear()

    @staticmethod
    def _next_reset(current_day: date) -> datetime:
        return datetime.combine(current_day + timedelta(days=1), time.min, tzinfo=timezone.utc)


daily_quota = InMemoryDailyQuota(
    llm_invocation_limit=settings.QUOTA.DAILY_LLM_INVOCATIONS,
    user_action_limit=settings.QUOTA.DAILY_USER_ACTIONS,
)
