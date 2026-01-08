import logging
import os

DEFAULT_MAX_PAGINATION_PAGES = 10_000
DEFAULT_MAX_PAGINATION_ITEMS = 1_000_000

ENV_MAX_PAGINATION_PAGES = "CARTOGRAPHY_MAX_PAGINATION_PAGES"
ENV_MAX_PAGINATION_ITEMS = "CARTOGRAPHY_MAX_PAGINATION_ITEMS"


def _get_env_int(
    name: str,
    default: int,
    logger: logging.Logger | None = None,
) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        return default
    try:
        value = int(raw_value)
    except ValueError:
        if logger:
            logger.warning(
                "Invalid %s=%r; using default %d.",
                name,
                raw_value,
                default,
            )
        return default
    if value <= 0:
        if logger:
            logger.warning(
                "Non-positive %s=%d; using default %d.",
                name,
                value,
                default,
            )
        return default
    return value


def get_pagination_limits(logger: logging.Logger | None = None) -> tuple[int, int]:
    return (
        _get_env_int(
            ENV_MAX_PAGINATION_PAGES,
            DEFAULT_MAX_PAGINATION_PAGES,
            logger,
        ),
        _get_env_int(
            ENV_MAX_PAGINATION_ITEMS,
            DEFAULT_MAX_PAGINATION_ITEMS,
            logger,
        ),
    )
