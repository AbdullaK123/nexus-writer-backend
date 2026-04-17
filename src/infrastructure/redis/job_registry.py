"""Redis-backed job registry for tracking job status and tags.

Replaces Prefect's flow run tracking with a thin Redis layer.
Supports tag-based filtering and predecessor ordering.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum

from redis.asyncio import Redis

from src.shared.utils.logging_context import get_layer_logger, LAYER_INFRA

log = get_layer_logger(LAYER_INFRA)

_META_TTL = 86400 * 7  # 7 days


class RegistryStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobRegistry:
    """Thin Redis layer for job tracking with tag-based filtering."""

    def __init__(self, redis: Redis) -> None:
        self._r = redis

    async def register(self, job_id: str, tags: list[str], meta: dict[str, str] | None = None) -> None:
        """Register a job with tags and initial QUEUED status."""
        pipe = self._r.pipeline()
        fields: dict[str, str] = {
            "status": RegistryStatus.QUEUED,
            "tags": json.dumps(tags),
            "created_at": datetime.now(timezone.utc).isoformat(),
            **(meta or {}),
        }
        pipe.hset(f"job:{job_id}", mapping=fields)
        pipe.expire(f"job:{job_id}", _META_TTL)
        for tag in tags:
            pipe.sadd(f"jobs:tag:{tag}", job_id)
        await pipe.execute()

    async def set_status(self, job_id: str, status: RegistryStatus | str, **extra: str) -> None:
        """Update job status and optional metadata fields."""
        mapping: dict[str, str] = {"status": str(status)}
        if status == RegistryStatus.RUNNING:
            mapping["started_at"] = datetime.now(timezone.utc).isoformat()
        elif status in (RegistryStatus.COMPLETE, RegistryStatus.FAILED, RegistryStatus.CANCELLED):
            mapping["completed_at"] = datetime.now(timezone.utc).isoformat()
        mapping.update(extra)
        await self._r.hset(f"job:{job_id}", mapping=mapping)

    async def get_meta(self, job_id: str) -> dict[str, str] | None:
        """Get all metadata for a job."""
        data = await self._r.hgetall(f"job:{job_id}")
        if not data:
            return None
        return {
            (k.decode() if isinstance(k, bytes) else k): (v.decode() if isinstance(v, bytes) else v)
            for k, v in data.items()
        }

    async def get_tags(self, job_id: str) -> list[str]:
        """Get tags for a job."""
        raw = await self._r.hget(f"job:{job_id}", "tags")
        if not raw:
            return []
        return json.loads(raw.decode() if isinstance(raw, bytes) else raw)

    async def find_by_tags(
        self, tags: list[str], statuses: list[str] | None = None
    ) -> list[str]:
        """Find job IDs matching ALL tags, optionally filtered by status.

        Lazily cleans up stale set entries (expired meta hashes).
        """
        if not tags:
            return []

        keys = [f"jobs:tag:{tag}" for tag in tags]
        raw_ids = await self._r.sinter(*keys)
        job_ids = [jid.decode() if isinstance(jid, bytes) else jid for jid in raw_ids]

        if not statuses:
            return job_ids

        result: list[str] = []
        stale: list[str] = []
        for job_id in job_ids:
            status = await self._r.hget(f"job:{job_id}", "status")
            if status is None:
                stale.append(job_id)
                continue
            s = status.decode() if isinstance(status, bytes) else status
            if s in statuses:
                result.append(job_id)

        # Lazy cleanup of stale entries
        if stale:
            pipe = self._r.pipeline()
            for tag in tags:
                for job_id in stale:
                    pipe.srem(f"jobs:tag:{tag}", job_id)
            await pipe.execute()

        return result

    async def cleanup(self, job_id: str) -> None:
        """Remove all keys for a job (called after job completes)."""
        tags = await self.get_tags(job_id)
        pipe = self._r.pipeline()
        pipe.delete(f"job:{job_id}")
        for tag in tags:
            pipe.srem(f"jobs:tag:{tag}", job_id)
        await pipe.execute()
