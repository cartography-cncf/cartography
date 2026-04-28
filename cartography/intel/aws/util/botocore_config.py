import os
from functools import lru_cache
from typing import Any

import botocore.config

DEFAULT_READ_TIMEOUT = 120
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_RETRY_MODE = "standard"
VALID_RETRY_MODES = frozenset({"adaptive", "legacy", "standard"})

RETRY_MODE_ENV_VAR = "CARTOGRAPHY_AWS_RETRY_MODE"
MAX_ATTEMPTS_ENV_VAR = "CARTOGRAPHY_AWS_MAX_ATTEMPTS"
READ_TIMEOUT_ENV_VAR = "CARTOGRAPHY_AWS_READ_TIMEOUT"
LAMBDA_READ_TIMEOUT = 30
LAMBDA_MAX_ATTEMPTS = 2


def _get_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        return default
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"{name} must be a positive integer, got {raw_value!r}."
        ) from exc
    if value < 1:
        raise ValueError(f"{name} must be a positive integer, got {raw_value!r}.")
    return value


def _get_retry_mode_env(default: str) -> str:
    raw_value = os.getenv(RETRY_MODE_ENV_VAR)
    if raw_value is None or raw_value == "":
        return default
    retry_mode = raw_value.strip().lower()
    if retry_mode not in VALID_RETRY_MODES:
        supported_modes = ", ".join(sorted(VALID_RETRY_MODES))
        raise ValueError(
            f"{RETRY_MODE_ENV_VAR} must be one of {supported_modes}, got {raw_value!r}."
        )
    return retry_mode


def _normalize_retries(
    config: botocore.config.Config,
    *,
    max_attempts: int,
    retry_mode: str,
) -> botocore.config.Config:
    # Botocore mutates Config.retries during client creation by replacing
    # max_attempts with total_max_attempts. Reset the shared config object so
    # callers always see the contract Cartography expects.
    config.retries = {
        "max_attempts": max_attempts,
        "mode": retry_mode,
    }
    return config


@lru_cache(maxsize=None)
def _get_botocore_config(
    *,
    read_timeout: int = DEFAULT_READ_TIMEOUT,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    retry_mode: str = DEFAULT_RETRY_MODE,
    max_pool_connections: int | None = None,
) -> botocore.config.Config:
    kwargs: dict[str, object] = {
        "read_timeout": read_timeout,
        "retries": {
            "max_attempts": max_attempts,
            "mode": retry_mode,
        },
    }
    if max_pool_connections is not None:
        kwargs["max_pool_connections"] = max_pool_connections
    return botocore.config.Config(**kwargs)


def get_botocore_config(
    *,
    read_timeout: int | None = None,
    max_attempts: int | None = None,
    retry_mode: str | None = None,
    max_pool_connections: int | None = None,
) -> botocore.config.Config:
    resolved_read_timeout = (
        read_timeout
        if read_timeout is not None
        else _get_int_env(READ_TIMEOUT_ENV_VAR, DEFAULT_READ_TIMEOUT)
    )
    resolved_max_attempts = (
        max_attempts
        if max_attempts is not None
        else _get_int_env(MAX_ATTEMPTS_ENV_VAR, DEFAULT_MAX_ATTEMPTS)
    )
    resolved_retry_mode = (
        retry_mode
        if retry_mode is not None
        else _get_retry_mode_env(DEFAULT_RETRY_MODE)
    )
    return _normalize_retries(
        _get_botocore_config(
            read_timeout=resolved_read_timeout,
            max_attempts=resolved_max_attempts,
            retry_mode=resolved_retry_mode,
            max_pool_connections=max_pool_connections,
        ),
        max_attempts=resolved_max_attempts,
        retry_mode=resolved_retry_mode,
    )


def get_lambda_botocore_config(
    *,
    read_timeout: int | None = None,
    max_attempts: int | None = None,
    retry_mode: str | None = None,
    max_pool_connections: int | None = None,
) -> botocore.config.Config:
    return get_botocore_config(
        read_timeout=(
            read_timeout if read_timeout is not None else LAMBDA_READ_TIMEOUT
        ),
        max_attempts=(
            max_attempts if max_attempts is not None else LAMBDA_MAX_ATTEMPTS
        ),
        retry_mode=retry_mode,
        max_pool_connections=max_pool_connections,
    )


def _create_client(
    session: Any,
    service_name: str,
    *args: Any,
    config: botocore.config.Config | None = None,
    **kwargs: Any,
) -> Any:
    return session.client(
        service_name,
        *args,
        config=config or get_botocore_config(),
        **kwargs,
    )


def create_boto3_client(
    session: Any,
    service_name: str,
    *args: Any,
    config: botocore.config.Config | None = None,
    **kwargs: Any,
) -> Any:
    return _create_client(
        session,
        service_name,
        *args,
        config=config,
        **kwargs,
    )


def create_boto3_resource(
    session: Any,
    service_name: str,
    *args: Any,
    config: botocore.config.Config | None = None,
    **kwargs: Any,
) -> Any:
    return session.resource(
        service_name,
        *args,
        config=config or get_botocore_config(),
        **kwargs,
    )


def create_aioboto3_client(
    session: Any,
    service_name: str,
    *args: Any,
    config: botocore.config.Config | None = None,
    **kwargs: Any,
) -> Any:
    return _create_client(
        session,
        service_name,
        *args,
        config=config,
        **kwargs,
    )
