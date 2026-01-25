import botocore.config


def get_botocore_config() -> botocore.config.Config:
    """
    Returns a botocore config with retry settings for Bedrock API calls.

    Bedrock management APIs have rate limits (e.g., GetAgent: 15 RPS).
    This config provides automatic retry with exponential backoff for throttling.
    """
    return botocore.config.Config(
        read_timeout=360,
        retries={
            "max_attempts": 10,
            "mode": "adaptive",  # Adaptive retry mode for better throttling handling
        },
    )
