from typing import Optional
from loguru import logger, Record
import sys

from src.shared.utils.correlation import get_correlation_id, get_user_id

LAYER_APP = "app"
LAYER_SERVICE = "service"
LAYER_DATA = "data"
LAYER_INFRA = "infrastructure"
LAYER_SHARED = "shared"

LAYERS = (LAYER_APP, LAYER_SERVICE, LAYER_INFRA, LAYER_DATA, LAYER_SHARED)

LAYER_COLORS = {
    LAYER_APP:     "<magenta>",
    LAYER_SERVICE: "<cyan>",
    LAYER_INFRA:   "<yellow>",
    LAYER_DATA:    "<green>",
    LAYER_SHARED:  "<white>",
}

LAYER_BADGES = {
    LAYER_APP:     "[APP]   ",
    LAYER_SERVICE: "[SVC]   ",
    LAYER_INFRA:   "[INFRA] ",
    LAYER_DATA:    "[DATA]  ",
    LAYER_SHARED:  "[SHARED]",
}


def detect_layer(name: Optional[str]) -> str:
    if not name:
        return LAYER_SHARED
    parts = name.split(".")
    return parts[1] if len(parts) >= 2 and parts[0] == "src" else LAYER_SHARED


def context_logger(**extra):
    extra.pop("correlation_id", None)
    extra.pop("user_id", None)
    return logger.bind(
        correlation_id=get_correlation_id(),
        user_id=get_user_id(),
        **extra,
    )


def format_record(record: Record) -> str:
    layer = record["extra"].get("layer") or detect_layer(record["name"])
    color = LAYER_COLORS.get(layer, "<white>")
    badge = LAYER_BADGES.get(layer, "[????] ")
    return (
        "<dim>{time:HH:mm:ss.SSS}</dim> "
        f"{color}<bold>{badge}</bold></> "
        "<level>{level: <8}</level> "
        "<blue>{name}</blue>:<blue>{function}</blue>:<blue>{line}</blue> "
        "- <level>{message}</level>"
        "\n{exception}"
    )


def layer_filter(target: str):
    def _f(record: Record) -> bool:
        layer = record["extra"].get("layer") or detect_layer(record["name"])
        return layer == target
    return _f


def _add_layer_sinks(layer: str) -> None:
    base = dict(
        format=format_record,
        filter=layer_filter(layer),
        colorize=False,
        compression="gz",
        enqueue=True,
    )
    logger.add(
        f"logs/{layer}/{{time:YYYY-MM-DD}}.log",
        level="INFO",
        rotation="20 MB",
        retention="14 days",
        **base,
    )
    logger.add(
        f"logs/{layer}/errors.log",
        level="ERROR",
        rotation="1 week",
        retention="90 days",
        backtrace=True,
        diagnose=False,
        **base,
    )


def configure_logger() -> None:
    logger.remove()

    logger.add(sys.stderr, format=format_record, colorize=True, level="DEBUG")

    for layer in LAYERS:
        _add_layer_sinks(layer)

    logger.add(
        "logs/app.jsonl",
        serialize=True,
        level="INFO",
        rotation="50 MB",
        retention=20,
        compression="gz",
        enqueue=True,
    )