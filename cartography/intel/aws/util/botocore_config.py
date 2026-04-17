from functools import lru_cache
from typing import Any

import botocore.config


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
    read_timeout: int = 120,
    max_attempts: int = 10,
    retry_mode: str = "adaptive",
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
    read_timeout: int = 120,
    max_attempts: int = 10,
    retry_mode: str = "adaptive",
    max_pool_connections: int | None = None,
) -> botocore.config.Config:
    return _normalize_retries(
        _get_botocore_config(
            read_timeout=read_timeout,
            max_attempts=max_attempts,
            retry_mode=retry_mode,
            max_pool_connections=max_pool_connections,
        ),
        max_attempts=max_attempts,
        retry_mode=retry_mode,
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
