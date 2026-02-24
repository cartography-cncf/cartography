import asyncio
import os
from dataclasses import dataclass
from typing import Any
from typing import Coroutine
from typing import TypeVar

from aiobotocore.config import AioConfig

T = TypeVar("T")


@dataclass(frozen=True)
class AwsAsyncTuning:
    max_concurrent_requests: int = 100
    max_concurrent_buckets: int = 25
    max_concurrent_repositories: int = 50
    max_pool_connections: int = 100
    retry_mode: str = "standard"
    max_attempts: int = 10
    read_timeout: int = 120
    connect_timeout: int = 10

    @classmethod
    def from_env(cls) -> "AwsAsyncTuning":
        def _get_int(name: str, default: int) -> int:
            raw = os.getenv(name)
            if raw is None:
                return default
            try:
                value = int(raw)
            except ValueError:
                return default
            return value if value > 0 else default

        max_concurrency = _get_int(
            "CARTOGRAPHY_AWS_ASYNC_MAX_CONCURRENCY",
            cls.max_concurrent_requests,
        )
        return cls(
            max_concurrent_requests=max_concurrency,
            max_concurrent_buckets=_get_int(
                "CARTOGRAPHY_AWS_ASYNC_MAX_BUCKET_CONCURRENCY",
                cls.max_concurrent_buckets,
            ),
            max_concurrent_repositories=_get_int(
                "CARTOGRAPHY_AWS_ASYNC_MAX_REPO_CONCURRENCY",
                cls.max_concurrent_repositories,
            ),
            max_pool_connections=_get_int(
                "CARTOGRAPHY_AWS_ASYNC_MAX_POOL_CONNECTIONS",
                cls.max_pool_connections,
            ),
            max_attempts=_get_int(
                "CARTOGRAPHY_AWS_ASYNC_MAX_ATTEMPTS",
                cls.max_attempts,
            ),
        )


def build_aio_config(tuning: AwsAsyncTuning) -> AioConfig:
    return AioConfig(
        read_timeout=tuning.read_timeout,
        connect_timeout=tuning.connect_timeout,
        max_pool_connections=tuning.max_pool_connections,
        retries={"mode": tuning.retry_mode, "max_attempts": tuning.max_attempts},
    )


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)
