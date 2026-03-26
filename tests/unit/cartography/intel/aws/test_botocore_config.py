from cartography.intel.aws.bedrock.util import get_botocore_config as get_bedrock_config
from cartography.intel.aws.ec2.util import get_botocore_config as get_ec2_config
from cartography.intel.aws.util.botocore_config import get_botocore_config


def test_get_botocore_config_defaults_to_adaptive_retries():
    config = get_botocore_config()

    assert config.retries["max_attempts"] == 10
    assert config.retries["mode"] == "adaptive"
    assert config.read_timeout == 360


def test_get_botocore_config_supports_pool_and_retry_overrides():
    config = get_botocore_config(max_pool_connections=50, max_attempts=8)

    assert config.max_pool_connections == 50
    assert config.retries["max_attempts"] == 8
    assert config.retries["mode"] == "adaptive"


def test_get_botocore_config_is_memoized_for_same_arguments():
    config_one = get_botocore_config(max_pool_connections=50)
    config_two = get_botocore_config(max_pool_connections=50)

    assert config_one is config_two


def test_ec2_and_bedrock_helpers_share_the_common_config_builder():
    assert get_ec2_config() is get_botocore_config()
    assert get_bedrock_config() is get_botocore_config()
