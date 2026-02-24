import asyncio

from cartography.intel.aws.util.async_runtime import AwsAsyncTuning
from cartography.intel.aws.util.async_runtime import build_aio_config
from cartography.intel.aws.util.async_runtime import run_async


def test_aws_async_tuning_from_env(monkeypatch):
    monkeypatch.setenv("CARTOGRAPHY_AWS_ASYNC_MAX_CONCURRENCY", "77")
    monkeypatch.setenv("CARTOGRAPHY_AWS_ASYNC_MAX_BUCKET_CONCURRENCY", "33")
    monkeypatch.setenv("CARTOGRAPHY_AWS_ASYNC_MAX_REPO_CONCURRENCY", "55")
    monkeypatch.setenv("CARTOGRAPHY_AWS_ASYNC_MAX_POOL_CONNECTIONS", "123")
    monkeypatch.setenv("CARTOGRAPHY_AWS_ASYNC_MAX_ATTEMPTS", "9")

    tuning = AwsAsyncTuning.from_env()

    assert tuning.max_concurrent_requests == 77
    assert tuning.max_concurrent_buckets == 33
    assert tuning.max_concurrent_repositories == 55
    assert tuning.max_pool_connections == 123
    assert tuning.max_attempts == 9


def test_build_aio_config():
    tuning = AwsAsyncTuning(
        max_pool_connections=222,
        retry_mode="standard",
        max_attempts=7,
        read_timeout=45,
        connect_timeout=12,
    )

    config = build_aio_config(tuning)

    assert config.max_pool_connections == 222
    assert config.retries["mode"] == "standard"
    assert config.retries["max_attempts"] == 7
    assert config.read_timeout == 45
    assert config.connect_timeout == 12


def test_run_async_from_sync_context():
    async def _demo():
        await asyncio.sleep(0)
        return "ok"

    assert run_async(_demo()) == "ok"
