from functools import lru_cache
from typing import Any

import botocore.config


@lru_cache(maxsize=None)
def get_botocore_config(
    *,
    read_timeout: int = 360,
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


def create_boto3_client(
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
    return session.client(
        service_name,
        *args,
        config=config or get_botocore_config(),
        **kwargs,
    )


class _WrappedBoto3Session:
    def __init__(self, session: Any, config: botocore.config.Config) -> None:
        self._session = session
        self._config = config

    def client(
        self,
        service_name: str,
        *args: Any,
        config: botocore.config.Config | None = None,
        **kwargs: Any,
    ) -> Any:
        return create_boto3_client(
            self._session,
            service_name,
            *args,
            config=config or self._config,
            **kwargs,
        )

    def resource(
        self,
        service_name: str,
        *args: Any,
        config: botocore.config.Config | None = None,
        **kwargs: Any,
    ) -> Any:
        return create_boto3_resource(
            self._session,
            service_name,
            *args,
            config=config or self._config,
            **kwargs,
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._session, name)


class _WrappedAioboto3Session:
    def __init__(self, session: Any, config: botocore.config.Config) -> None:
        self._session = session
        self._config = config

    def client(
        self,
        service_name: str,
        *args: Any,
        config: botocore.config.Config | None = None,
        **kwargs: Any,
    ) -> Any:
        return create_aioboto3_client(
            self._session,
            service_name,
            *args,
            config=config or self._config,
            **kwargs,
        )

    def resource(
        self,
        service_name: str,
        *args: Any,
        config: botocore.config.Config | None = None,
        **kwargs: Any,
    ) -> Any:
        return self._session.resource(
            service_name,
            *args,
            config=config or self._config,
            **kwargs,
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._session, name)


def wrap_boto3_session(
    session: Any,
    config: botocore.config.Config | None = None,
) -> Any:
    if isinstance(session, _WrappedBoto3Session):
        return session
    return _WrappedBoto3Session(session, config or get_botocore_config())


def wrap_aioboto3_session(
    session: Any,
    config: botocore.config.Config | None = None,
) -> Any:
    if isinstance(session, _WrappedAioboto3Session):
        return session
    return _WrappedAioboto3Session(session, config or get_botocore_config())
