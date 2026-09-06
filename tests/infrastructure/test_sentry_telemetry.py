from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import ValidationError

from src.infrastructure.config.settings import SentryConfig
from src.infrastructure.telemetry import sentry as sentry_telemetry


def test_init_sentry_is_noop_without_dsn(monkeypatch: pytest.MonkeyPatch) -> None:
    init_calls: list[dict[str, Any]] = []
    tag_calls: list[tuple[str, str]] = []

    monkeypatch.setattr(
        sentry_telemetry,
        "settings",
        SimpleNamespace(sentry_dsn=None, env="dev"),
    )
    monkeypatch.setattr(
        sentry_telemetry.sentry_sdk,
        "init",
        lambda **kwargs: init_calls.append(kwargs),
    )
    monkeypatch.setattr(
        sentry_telemetry.sentry_sdk,
        "set_tag",
        lambda key, value: tag_calls.append((key, value)),
    )

    sentry_telemetry.init_sentry("api")

    assert init_calls == []
    assert tag_calls == []


def test_init_sentry_uses_safe_runtime_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    init_calls: list[dict[str, Any]] = []
    tag_calls: list[tuple[str, str]] = []

    monkeypatch.setattr(
        sentry_telemetry,
        "settings",
        SimpleNamespace(
            sentry_dsn="https://public@example.invalid/1",
            env="staging",
        ),
    )
    monkeypatch.setattr(
        sentry_telemetry,
        "config",
        SimpleNamespace(sentry=SimpleNamespace(traces_sample_rate=0.25)),
    )
    monkeypatch.setattr(
        sentry_telemetry.sentry_sdk,
        "init",
        lambda **kwargs: init_calls.append(kwargs),
    )
    monkeypatch.setattr(
        sentry_telemetry.sentry_sdk,
        "set_tag",
        lambda key, value: tag_calls.append((key, value)),
    )

    sentry_telemetry.init_sentry("saq-worker")

    assert init_calls == [
        {
            "dsn": "https://public@example.invalid/1",
            "environment": "staging",
            "traces_sample_rate": 0.25,
            "send_default_pii": False,
            "max_request_body_size": "never",
        }
    ]
    assert tag_calls == [("service", "saq-worker")]


@pytest.mark.parametrize("sample_rate", [-0.01, 1.01])
def test_sentry_trace_sample_rate_rejects_out_of_range_values(
    sample_rate: float,
) -> None:
    with pytest.raises(ValidationError):
        SentryConfig(traces_sample_rate=sample_rate)


@pytest.mark.parametrize("sample_rate", [0.0, 1.0])
def test_sentry_trace_sample_rate_accepts_boundaries(sample_rate: float) -> None:
    assert SentryConfig(traces_sample_rate=sample_rate).traces_sample_rate == sample_rate
