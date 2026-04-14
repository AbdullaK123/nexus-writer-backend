from loguru import logger
import logging
import sys


# ── Layer identifiers ────────────────────────────────────────────────────────
LAYER_APP = "app"
LAYER_SERVICE = "service"
LAYER_DATA = "data"
LAYER_INFRA = "infra"
LAYER_SHARED = "shared"

ALL_LAYERS = {LAYER_APP, LAYER_SERVICE, LAYER_DATA, LAYER_INFRA, LAYER_SHARED}


# ── Stdlib → Loguru intercept handler ────────────────────────────────────────
class _InterceptHandler(logging.Handler):
    """Route stdlib logging records into loguru with the correct layer tag."""

    def emit(self, record: logging.LogRecord) -> None:
        # Determine layer from the stdlib logger name
        name = record.name
        if name.startswith("infrastructure"):
            layer = LAYER_INFRA
        elif name.startswith("data"):
            layer = LAYER_DATA
        elif name.startswith("service"):
            layer = LAYER_SERVICE
        else:
            layer = LAYER_SHARED

        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.bind(layer=layer).opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def _layer_filter(layer: str):
    """Return a loguru filter that passes only records tagged with *layer*."""
    return lambda record: record["extra"].get("layer") == layer


# ── Console format per layer (each layer gets its own color) ─────────────────
_CONSOLE_FORMATS = {
    LAYER_APP: (
        "<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
        "<blue><bold>[APP]</bold></blue> <blue>{name}</blue>:<blue>{function}</blue>:<blue>{line}</blue> "
        "- <level>{message}</level>"
    ),
    LAYER_SERVICE: (
        "<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
        "<magenta><bold>[SVC]</bold></magenta> <magenta>{name}</magenta>:<magenta>{function}</magenta>:<magenta>{line}</magenta> "
        "- <level>{message}</level>"
    ),
    LAYER_DATA: (
        "<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
        "<yellow><bold>[DAT]</bold></yellow> <yellow>{name}</yellow>:<yellow>{function}</yellow>:<yellow>{line}</yellow> "
        "- <level>{message}</level>"
    ),
    LAYER_INFRA: (
        "<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
        "<cyan><bold>[INF]</bold></cyan> <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
        "- <level>{message}</level>"
    ),
    LAYER_SHARED: (
        "<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
        "<white><bold>[SHR]</bold></white> <white>{name}</white>:<white>{function}</white>:<white>{line}</white> "
        "- <level>{message}</level>"
    ),
}

# Flat file format (no ANSI — used for all layer log files)
_FILE_FMT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"


# ── Layer → file settings ────────────────────────────────────────────────────
_LAYER_FILE_CFG = {
    LAYER_APP: {
        "path": "logs/app.log",
        "level": "INFO",
        "rotation": "25 MB",
        "retention": "30 days",
    },
    LAYER_SERVICE: {
        "path": "logs/service.log",
        "level": "DEBUG",
        "rotation": "30 MB",
        "retention": "30 days",
    },
    LAYER_DATA: {
        "path": "logs/data.log",
        "level": "DEBUG",
        "rotation": "20 MB",
        "retention": "14 days",
    },
    LAYER_INFRA: {
        "path": "logs/infra.log",
        "level": "DEBUG",
        "rotation": "20 MB",
        "retention": "14 days",
    },
    LAYER_SHARED: {
        "path": "logs/shared.log",
        "level": "DEBUG",
        "rotation": "10 MB",
        "retention": "14 days",
    },
}


def setup_logging():
    """Configure Loguru with per-layer console colors, log files, and cross-cutting files."""

    logger.remove()

    # ── Per-layer: colored console + dedicated log file ──────────────────
    for layer in ALL_LAYERS:
        # Console handler (colored, per-layer format)
        logger.add(
            sys.stdout,
            format=_CONSOLE_FORMATS[layer],
            level="INFO",
            colorize=True,
            enqueue=True,
            filter=_layer_filter(layer),
        )

        # Dedicated file handler
        cfg = _LAYER_FILE_CFG[layer]
        logger.add(
            cfg["path"],
            format=_FILE_FMT,
            level=cfg["level"],
            rotation=cfg["rotation"],
            retention=cfg["retention"],
            compression="zip",
            serialize=True,
            enqueue=True,
            filter=_layer_filter(layer),
        )

    # ── Fallback console for un-tagged log lines ─────────────────────────
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
            "<dim>{name}</dim>:<dim>{function}</dim>:<dim>{line}</dim> "
            "- <level>{message}</level>"
        ),
        level="INFO",
        colorize=True,
        enqueue=True,
        filter=lambda r: r["extra"].get("layer") not in ALL_LAYERS,
    )

    # ── Cross-cutting log files (layer-agnostic) ─────────────────────────

    # All errors regardless of layer
    logger.add(
        "logs/errors.log",
        format=_FILE_FMT,
        level="ERROR",
        rotation="10 MB",
        retention="60 days",
        compression="zip",
        serialize=True,
        enqueue=True,
    )

    logger.bind(layer=LAYER_INFRA).success("Logging system initialised — per-layer handlers active")

    # ── Route stdlib loggers (tenacity, etc.) through loguru ─────────────
    logging.basicConfig(handlers=[_InterceptHandler()], level=logging.DEBUG, force=True)
