from functools import lru_cache

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
