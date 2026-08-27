from types import SimpleNamespace

import cron_worker


async def test_session_cleanup_cron_invokes_cleanup_and_heartbeats(
    cron_runtime: SimpleNamespace,
) -> None:
    await cron_worker.run_session_cleanup_once()

    assert cron_runtime.session_cleanup.calls == 1
    assert cron_runtime.heartbeat.touch_count == 1


async def test_reextraction_cron_invokes_stale_regeneration_and_heartbeats(
    cron_runtime: SimpleNamespace,
) -> None:
    await cron_worker.run_reextraction_once()

    assert cron_runtime.reextraction.calls == 1
    assert cron_runtime.heartbeat.touch_count == 1


async def test_embedding_cron_invokes_pending_embedding_and_heartbeats(
    cron_runtime: SimpleNamespace,
) -> None:
    await cron_worker.run_embedding_once()

    assert cron_runtime.embedding.calls == 1
    assert cron_runtime.heartbeat.touch_count == 1


async def test_cron_failure_is_swallowed_and_does_not_block_unrelated_job(
    cron_runtime: SimpleNamespace,
) -> None:
    cron_runtime.reextraction.error = RuntimeError("reextraction failed")

    await cron_worker.run_reextraction_once()
    await cron_worker.run_embedding_once()

    assert cron_runtime.reextraction.calls == 1
    assert cron_runtime.embedding.calls == 1
    assert cron_runtime.heartbeat.touch_count == 2
