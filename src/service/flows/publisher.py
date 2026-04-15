"""Flow event publisher — thin wrapper around RedisPubSub for Prefect flows."""
from __future__ import annotations

import time
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel
from prefect import runtime

from src.data.schemas.jobs import FlowEvent, FlowEventType, JobType
from src.infrastructure.redis.pubsub import RedisPubSub
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE

log = get_layer_logger(LAYER_SERVICE)

D = TypeVar("D", bound=BaseModel)


class FlowPublisher(Generic[D]):
    """Scoped event publisher for a single flow run, generic over payload type D."""

    def __init__(
        self,
        user_id: str,
        story_id: str,
        job_type: JobType,
        total_steps: int,
        pubsub: RedisPubSub[FlowEvent[D]],
    ) -> None:
        self._user_id = user_id
        self._story_id = story_id
        self._job_type = job_type
        self._total_steps = total_steps
        self._job_run_id = str(runtime.flow_run.id or "unknown")
        self._pubsub = pubsub
        self._channel = self._pubsub.channel("flow", user_id, self._job_run_id)
        self._step = 0
        self._t0: float | None = None

    # ── convenience emitters ─────────────────────────────────────────

    async def flow_started(self, message: str | None = None, data: D | None = None) -> None:
        self._t0 = time.monotonic()
        await self._emit(FlowEventType.FLOW_STARTED, message=message, data=data)

    async def flow_complete(self, message: str | None = None, data: D | None = None) -> None:
        await self._emit(FlowEventType.FLOW_COMPLETE, message=message, data=data, with_duration=True)

    async def flow_failed(self, message: str | None = None, data: D | None = None) -> None:
        await self._emit(FlowEventType.FLOW_FAILED, message=message, data=data, with_duration=True)

    async def task_started(self, task_name: str, message: str | None = None, data: D | None = None) -> None:
        self._step += 1
        await self._emit(FlowEventType.TASK_STARTED, task=task_name, message=message, data=data)

    async def task_complete(self, task_name: str, message: str | None = None, data: D | None = None) -> None:
        await self._emit(FlowEventType.TASK_COMPLETE, task=task_name, message=message, data=data)

    async def task_failed(self, task_name: str, message: str | None = None, data: D | None = None) -> None:
        await self._emit(FlowEventType.TASK_FAILED, task=task_name, message=message, data=data)

    # ── internal ─────────────────────────────────────────────────────

    async def _emit(
        self,
        event_type: FlowEventType,
        *,
        task: str | None = None,
        message: str | None = None,
        data: D | None = None,
        with_duration: bool = False,
    ) -> None:
        duration_ms: int | None = None
        if with_duration and self._t0 is not None:
            duration_ms = int((time.monotonic() - self._t0) * 1000)

        event = FlowEvent[D]( #type: ignore
            job_run_id=self._job_run_id,
            user_id=self._user_id,
            story_id=self._story_id,
            event_type=event_type,
            job_type=self._job_type,
            task=task,
            message=message,
            data=data,
            step=self._step if self._step > 0 else None,
            total_steps=self._total_steps,
            duration_ms=duration_ms,
        )

        try:
            await self._pubsub.publish(self._channel, event)
        except Exception:
            log.warning("flow_publisher.publish_failed", event_type=event_type.value, task=task)


def create_flow_pubsub(redis_url: str, model: type[D]) -> RedisPubSub[FlowEvent[D]]:
    """Factory for a typed flow event pubsub client."""
    return RedisPubSub(redis_url, FlowEvent[model]) #type: ignore
