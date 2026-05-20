import botocore.config


# TODO memoize this
def get_botocore_config() -> botocore.config.Config:
    return botocore.config.Config(
        read_timeout=360,
        connect_timeout=120,
        retries={
            'max_attempts': 1,
            'mode': 'standard',
        },
    )
